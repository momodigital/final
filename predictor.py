# predictor.py
"""
🏆 FINAL PREDICTOR - CORE LOGIC (Cleaned for Streamlit)
"""

import os
import random
from collections import Counter
from typing import List, Dict, Any, Optional
import functools

# ================== TURSO CONFIG ==================
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
    raise EnvironmentError("❌ TURSO_DATABASE_URL dan TURSO_AUTH_TOKEN harus di-set di environment variables!")

try:
    import libsql_client as libsql
except ImportError:
    raise ImportError("❌ libsql-client belum terinstall! Jalankan: pip install libsql-client")


class Colors:
    """Hanya untuk internal, tidak dipakai di Streamlit"""
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'


class TogelPredictor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.raw_data = data
        self.results: List[str] = [d['result'] for d in data 
                                  if isinstance(d.get('result'), str) and len(d['result']) == 4]
        self._cache: Dict[str, Any] = {}

    @functools.lru_cache(maxsize=32)
    def _get_digit_counter(self, position: Optional[str] = None) -> Counter:
        if not self.results:
            return Counter()
        if position is None:
            return Counter(d for num in self.results for d in num)
        
        idx_map = {'KOP': 1, 'KEPALA': 2, 'EKOR': 3}
        idx = idx_map.get(position)
        return Counter(num[idx] for num in self.results) if idx is not None else Counter()

    def get_top_digits(self, limit: int = 6) -> List[str]:
        if len(self.results) < 5:
            return [str(i) for i in range(10)][:limit]
        
        weights = {'AS': 0.15, 'KOP': 0.15, 'KEPALA': 0.20, 'EKOR': 0.50}
        weighted = Counter()
        for pos, w in weights.items():
            idx = {'AS': 0, 'KOP': 1, 'KEPALA': 2, 'EKOR': 3}[pos]
            for num in self.results:
                weighted[num[idx]] += w
        return [d for d, _ in weighted.most_common(limit)]

    def get_mistik(self, top_digits: List[str]) -> Dict[str, List[str]]:
        M_LAMA = {'0':'1','2':'5','3':'8','4':'7','5':'2','6':'9','7':'4','8':'3','9':'6'}
        M_BARU = {'0':'8','1':'7','2':'6','3':'9','4':'5','5':'4','6':'2','7':'1','8':'0','9':'3'}
        tua = [M_LAMA.get(d, d) for d in top_digits]
        baru = [M_BARU.get(d, d) for d in top_digits]
        return {'all_mistik': list(dict.fromkeys(tua + baru))}

    def get_index(self, top_digits: List[str]) -> List[str]:
        IDX = {'0':'5','1':'6','2':'7','3':'8','4':'9'}
        return list(dict.fromkeys(IDX.get(d, d) for d in top_digits))

    def get_ct_5d(self) -> str:
        if 'ct5' in self._cache:
            return self._cache['ct5']
        
        digits_w = []
        for i, num in enumerate(self.results):
            d = num[3]
            weight = 3.0 if i < 40 else 1.0
            digits_w.extend([d] * int(weight * 10))
        
        top3 = [d for d, _ in Counter(digits_w).most_common(10)]
        top_global = self.get_top_digits(10)
        mistik = self.get_mistik(top_global)['all_mistik']
        index_r = self.get_index(top_global)
        
        combined, seen = [], set()
        for d in top3 + mistik + index_r:
            if d not in seen:
                seen.add(d)
                combined.append(d)
            if len(combined) == 5:
                break
        result = ''.join(combined)
        self._cache['ct5'] = result
        return result

    def get_ct_3d(self) -> str:
        if 'ct3' in self._cache:
            return self._cache['ct3']

        recent = self.results[:20]
        if len(recent) < 10:
            recent = self.results

        kepala_weight = Counter()
        ekor_weight = Counter()
        for i, num in enumerate(recent):
            weight = 3.0 if i < 8 else 1.5 if i < 15 else 1.0
            kepala_weight[num[2]] += weight
            ekor_weight[num[3]] += weight

        digits_w = []
        for i, num in enumerate(self.results):
            base_weight = 3.0 if i < 40 else 1.0
            kep_boost = kepala_weight[num[2]] * 1.8
            eko_boost = ekor_weight[num[3]] * 1.6
            digits_w.extend([num[2]] * int(base_weight * kep_boost))
            digits_w.extend([num[3]] * int(base_weight * eko_boost))

        top = [d for d, _ in Counter(digits_w).most_common(12)]
        top_global = self.get_top_digits(12)
        mistik = self.get_mistik(top_global)['all_mistik']
        index_r = self.get_index(top_global)
        ct5 = list(self.get_ct_5d())

        combined = []
        seen = set()
        for group in [ct5[:3], top, mistik, index_r, top_global]:
            for d in group:
                if d not in seen:
                    seen.add(d)
                    combined.append(d)
                if len(combined) == 5:
                    break
            if len(combined) == 5:
                break

        result = ''.join(combined[:4])
        self._cache['ct3'] = result
        return result

    def get_top_by_position(self, position: str, limit: int = 8, use_mistik: bool = False) -> List[str]:
        if len(self.results) < 10:
            return [str(i) for i in range(10)][:limit]

        freq = self._get_digit_counter(position)

        if position == 'EKOR':
            recent = self.results[:30]
            recent_ekor = Counter(num[3] for num in recent)
            for d, count in recent_ekor.items():
                freq[d] += count * 2.5

            ct5 = set(self.get_ct_5d())
            ct3 = set(self.get_ct_3d())
            for d in ct5 | ct3:
                freq[d] += 12

        if use_mistik:
            top_global = self.get_top_digits(10)
            mistik = self.get_mistik(top_global)['all_mistik']
            index_r = self.get_index(top_global)
            for d in mistik + index_r:
                freq[d] += 9 if position == 'EKOR' else 8

        return [d for d, _ in freq.most_common(15)][:limit]

    def generate_bbfs_8d(self) -> List[str]:
        if 'bbfs' in self._cache:
            return self._cache['bbfs']
        
        top6 = self.get_top_digits(6)
        mistik = self.get_mistik(top6)['all_mistik']
        index_r = self.get_index(top6)
        
        cand = Counter()
        cand.update({d:100 for d in (top6 + mistik + index_r)[:6]})
        cand.update({d:90 for d in top6[:4]})
        cand.update({d:80 for d in top6})
        cand.update({d:70 for d in mistik})
        cand.update({d:60 for d in index_r})
        
        res = [d for d, _ in cand.most_common(20)]
        for i in range(10):
            d = str(i)
            if d not in res and len(res) < 8:
                res.append(d)
        
        result = res[:8]
        self._cache['bbfs'] = result
        return result

    def generate_bbfs_plus_one(self, bbfs_8d: List[str]) -> Dict[str, Any]:
        used = set(bbfs_8d)
        freq = self._get_digit_counter()
        candidates = [(d, freq.get(d, 0)) for d in '0123456789' if d not in used]
        plus = max(candidates, key=lambda x: x[1])[0] if candidates else '0'
        return {'bbfs': bbfs_8d, 'plus': plus}

    def get_unique_8d(self, list1: List[str], list2: List[str]) -> str:
        seen = set()
        combined = []
        for d in list1 + list2:
            if d not in seen:
                seen.add(d)
                combined.append(d)
            if len(combined) == 8:
                break
        for i in range(10):
            d = str(i)
            if d not in seen and len(combined) < 8:
                combined.append(d)
        return ''.join(combined[:8])

    def _get_weighted_candidates(self, digits: List[str], boost: List[str] = None) -> List[tuple]:
        freq = self._get_digit_counter()
        boost_set = set(boost or [])
        return [(d, max(freq.get(d, 0)*10 + (150 if d in boost_set else 0) + 
                        (80 if d in self.get_ct_5d() else 0), 10)) 
                for d in digits]

    def weighted_choice(self, candidates: List[tuple]) -> str:
        total = sum(w for _, w in candidates)
        r = random.uniform(0, total)
        upto = 0
        for digit, weight in candidates:
            upto += weight
            if upto >= r:
                return digit
        return candidates[-1][0]

    # ================== TOP 2D, 3D, 4D ==================
    def generate_top_2d_filtered(self, limit: int = 80) -> List[str]:
        ct5_set = set(self.get_ct_5d())
        kepala_set = set(self.get_top_by_position('KEPALA', 10, use_mistik=True))
        ekor_set = set(self.get_top_by_position('EKOR', 10, use_mistik=True))

        candidates = []
        for i in range(100):
            num = f"{i:02d}"
            d1, d2 = num[0], num[1]
            if d1 not in ct5_set and d2 not in ct5_set:
                continue
            if d1 not in kepala_set or d2 not in ekor_set:
                continue
            score = 0
            if d1 in ct5_set: score += 40
            if d2 in ct5_set: score += 40
            candidates.append((num, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in candidates[:limit]]

    def generate_top_3d_filtered(self, limit: int = 15) -> List[str]:
        bbfs_list = self.generate_bbfs_8d()
        plus = self.generate_bbfs_plus_one(bbfs_list)['plus']
        bbfs_set = set(bbfs_list + [plus])
        ct5_set = set(self.get_ct_5d())
        ct3_set = set(self.get_ct_3d())
        top_global = self.get_top_digits(10)
        mistik = set(self.get_mistik(top_global)['all_mistik'])
        index_r = set(self.get_index(top_global))
        strong_head = ct5_set | bbfs_set | mistik | index_r
        top2d = self.generate_top_2d_filtered(60)

        candidates = []
        seen = set()
        for _ in range(3000):
            head = self.weighted_choice(self._get_weighted_candidates(list(strong_head), list(ct5_set)))
            tail2d = random.choice(top2d[:35])
            combo = head + tail2d
            if combo in seen:
                continue
            seen.add(combo)
            score = 0
            if head in ct5_set: score += 45
            elif head in mistik: score += 30
            elif head in index_r: score += 25
            for d in tail2d:
                if d in ct5_set: score += 35
                elif d in mistik: score += 20
                elif d in index_r: score += 18
            if len(set(combo) & ct5_set) >= 2:
                score += 35
            if score >= 75:
                candidates.append((combo, score))
            if len(candidates) >= limit * 4:
                break
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in candidates[:limit]]

    def generate_top_4d_filtered(self, limit: int = 12) -> List[str]:
        bbfs_list = self.generate_bbfs_8d()
        plus = self.generate_bbfs_plus_one(bbfs_list)['plus']
        bbfs_set = set(bbfs_list + [plus])
        ct5_set = set(self.get_ct_5d())
        ct3_set = set(self.get_ct_3d())
        top_global = self.get_top_digits(10)
        mistik = set(self.get_mistik(top_global)['all_mistik'])
        index_r = set(self.get_index(top_global))
        as_candidates = [d for d in bbfs_list if d in ct5_set] or bbfs_list[:5]
        strong_set = ct5_set | bbfs_set | mistik | index_r | ct3_set

        candidates = []
        seen = set()
        for _ in range(4000):
            d1 = self.weighted_choice(self._get_weighted_candidates(as_candidates, list(ct5_set)))
            d2 = self.weighted_choice(self._get_weighted_candidates(list(strong_set), list(ct5_set)))
            d3 = self.weighted_choice(self._get_weighted_candidates(list(strong_set), list(ct5_set)))
            d4 = self.weighted_choice(self._get_weighted_candidates(list(strong_set), list(ct5_set)))
            combo = d1 + d2 + d3 + d4
            if combo in seen:
                continue
            seen.add(combo)
            score = sum(1 for d in combo if d in ct5_set) * 45
            score += sum(1 for d in combo if d in mistik) * 28
            score += sum(1 for d in combo if d in index_r) * 25
            score += sum(1 for d in combo if d in bbfs_set) * 18
            if combo[0] in ct5_set: score += 35
            if combo[3] in ct5_set: score += 30
            if len(set(combo)) < 3: score -= 80
            if score >= 130:
                candidates.append((combo, score))
            if len(candidates) >= limit * 5:
                break
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in candidates[:limit]]

    def analyze_history(self, limit: int = 10) -> List[Dict]:
        if len(self.raw_data) < limit + 5:
            return []
        history = []
        for i in range(limit):
            test = self.raw_data[i]
            train = self.raw_data[i+1:i+11]
            pred = TogelPredictor(train)
            actual = test.get('result', '')
            if len(actual) != 4:
                continue

            eko_pred = set(pred.get_top_by_position('EKOR', 10, use_mistik=True) + 
                          list(pred.get_ct_5d()) + list(pred.get_ct_3d()))

            history.append({
                'tanggal': str(test.get('tanggal',''))[:10],
                'result': actual,
                'ct5_hit': any(d in actual for d in pred.get_ct_5d()),
                'ct3_hit': any(d in actual for d in pred.get_ct_3d()),
                'bbfs_hit': any(d in actual for d in pred.generate_bbfs_8d()),
                'kop_hit': actual[1] in pred.get_top_by_position('KOP',8,True),
                'kepala_hit': actual[2] in pred.get_top_by_position('KEPALA',8,True),
                'ekor_hit': actual[3] in eko_pred,
            })
        return history

    def calculate_accuracy(self, history: List[Dict]) -> Dict[str, float]:
        if not history:
            return {"overall": 0.0}
        ct5 = sum(1 for h in history if h['ct5_hit']) / len(history) * 100
        ct3 = sum(1 for h in history if h['ct3_hit']) / len(history) * 100
        bbfs = sum(1 for h in history if h['bbfs_hit']) / len(history) * 100
        return {"overall": round((ct5 + ct3 + bbfs) / 3, 1)}

    def get_confidence_score(self) -> int:
        score = 65 + len(set(self.get_ct_5d())) * 4 + len(set(self.get_ct_3d())) * 5
        return min(98, max(55, score))


# ================== DATABASE HELPER ==================
async def get_pasaran_data(pasaran_name: str, limit: int = 200) -> List[Dict]:
    try:
        async with libsql.create_client(url=TURSO_DATABASE_URL, auth_token=TURSO_AUTH_TOKEN) as conn:
            result = await conn.execute(
                "SELECT result, tanggal FROM results_togel WHERE pasaran = ? ORDER BY tanggal DESC LIMIT ?",
                (pasaran_name, limit)
            )
            data = []
            for row in result.rows:
                res_str = ''.join(c for c in str(row[0]) if c.isdigit()).zfill(4)[:4]
                if len(res_str) == 4:
                    data.append({'result': res_str, 'tanggal': str(row[1] or '')})
            return data
    except Exception as e:
        raise Exception(f"Gagal mengambil data {pasaran_name}: {str(e)}")
