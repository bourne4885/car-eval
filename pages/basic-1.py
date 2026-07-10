import tkinter as tk
from tkinter import messagebox
import math

# ==========================================
# 1. 자동차 진단평가 가격 계산 엔진 (백엔드)
# ==========================================
class CarEvaluator:
    def __init__(self, is_import: bool, displacement: int, reg_year: int, reg_month: int, mileage: int, base_price_manwon: int):
        self.is_import = is_import
        self.displacement = displacement
        self.reg_year = reg_year
        self.reg_month = reg_month
        self.mileage = mileage
        self.base_price_manwon = base_price_manwon
        
        self.current_year = 2026
        self.current_month = 6

    def get_tier_and_coefficient(self):
        """[제7조] 승용형 자동차 등급 및 등급계수 산출"""
        if self.displacement >= 3600: tier = "특C"
        elif self.displacement >= 2900: tier = "특B"
        elif self.displacement >= 2400: tier = "특A"
        elif self.displacement >= 2100: tier = "I"
        elif self.displacement >= 1700: tier = "II"
        elif self.displacement >= 1300: tier = "III"
        elif self.displacement >= 1100: tier = "IV"
        else: tier = "경"

        coefficients = {
            "국산": {"특C": 2.2, "특B": 1.8, "특A": 1.5, "I": 1.4, "II": 1.2, "III": 1.0, "IV": 0.9, "경": 0.8},
            "수입": {"특C": 2.7, "특B": 2.5, "특A": 2.0, "I": 1.7, "II": 1.4, "III": 1.2, "IV": 1.1, "경": 1.0}
        }
        return tier, coefficients["수입" if self.is_import else "국산"][tier]

    def get_usage_period_and_coefficient(self):
        """[제8조] 사용년 계수 산출"""
        usage_years = self.current_year - self.reg_year
        remaining_months = self.current_month - self.reg_month
        usage_months = (usage_years * 12) + remaining_months
        
        if not self.is_import:
            age_coef = 1.0 if usage_years <= 2 else (0.9 if usage_years == 3 else (0.8 if usage_years == 4 else 0.7))
        else:
            age_coef = 1.0 if usage_years <= 2 else (0.9 if usage_years in [3, 4] else (0.8 if usage_years in [5, 6] else 0.7))
        return usage_years, usage_months, age_coef


# ==========================================
# 2. 모색도 그리기 및 종합 GUI 화면 (프런트엔드)
# ==========================================
class CarAssessmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 자동차진단평가 가치산출 마스터 시스템 (2026 검정용)")
        self.root.geometry("900(750)")
        self.root.resizable(False, False)

        # 실시간 상태 표시도 데이터 기록 보관소
        self.selected_damage = {}

        # 랭크별 기본 감점 점수 (제22조 기준 반영 뼈대)
        self.rank_base_points = {
            "외판1랭크": 15,
            "외판2랭크": 30,
            "주요골격A": 50,
            "주요골격B": 80,
            "주요골격C": 120
        }

        # 상단 차량 기본 정보 입력 폼 프레임
        info_frame = tk.LabelFrame(root, text=" 📝 차량 기본 데이터 입력 ", font=("Arial", 10, "bold"), padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=15, pady=5)

        # 입력 필드들 배치
        tk.Label(info_frame, text="구분:").grid(row=0, column=0, sticky=tk.W)
        self.origin_var = tk.StringVar(value="국산")
        tk.OptionMenu(info_frame, self.origin_var, "국산", "수입").grid(row=0, column=1, padx=5)

        tk.Label(info_frame, text="배기량(cc):").grid(row=0, column=2, sticky=tk.W)
        self.entry_disp = tk.Entry(info_frame, width=8)
        self.entry_disp.insert(0, "2000")
        self.entry_disp.grid(row=0, column=3, padx=5)

        tk.Label(info_frame, text="최초등록(년):").grid(row=0, column=4, sticky=tk.W)
        self.entry_year = tk.Entry(info_frame, width=6)
        self.entry_year.insert(0, "2023")
        self.entry_year.grid(row=0, column=5, padx=5)

        tk.Label(info_frame, text="주행거리(km):").grid(row=0, column=6, sticky=tk.W)
        self.entry_mileage = tk.Entry(info_frame, width=10)
        self.entry_mileage.insert(0, "50000")
        self.entry_mileage.grid(row=0, column=7, padx=5)

        tk.Label(info_frame, text="기준가격(만원):").grid(row=0, column=8, sticky=tk.W)
        self.entry_price = tk.Entry(info_frame, width=10)
        self.entry_price.insert(0, "3000")
        self.entry_price.grid(row=0, column=9, padx=5)

        # 중간 섹션: 자동차 모색도 배치 공간
        canvas_frame = tk.LabelFrame(root, text=" 🚘 자동차 상태 표시도 (클릭하여 상태 등록) ", font=("Arial", 10, "bold"))
        canvas_frame.pack(padx=15, pady=5)

        self.canvas = tk.Canvas(canvas_frame, width=850, height=260, bg="#f5f5f5", highlightthickness=0)
        self.canvas.pack(pady=5)

        # 모색도용 좌표 세팅 (박스 중심 타겟팅용)
        self.regions = {
            "후드": {"box": (50, 80, 150, 160), "rank": "외판1랭크"},
            "앞도어(좌)": {"box": (170, 30, 270, 90), "rank": "외판1랭크"},
            "앞도어(우)": {"box": (170, 150, 270, 210), "rank": "외판1랭크"},
            "사이드멤버(좌)": {"box": (60, 180, 180, 205), "rank": "주요골격B"},
            "사이드멤버(우)": {"box": (60, 215, 180, 240), "rank": "주요골격B"},
            "쿼터패널": {"box": (420, 40, 520, 100), "rank": "외판2랭크"},
            "트렁크리드": {"box": (540, 80, 620, 160), "rank": "외판1랭크"}
        }

        self.draw_car_vector()
        self.canvas.bind("<Button-1>", self.on_diagram_click)

        # 하단 기록현황 및 결과 도출창
        self.status_box = tk.Text(root, height=5, width=105, bg="#fafafa", font=("Consolas", 9))
        self.status_box.pack(padx=15, pady=5)
        self.status_box.insert(tk.END, "현재 감가 이력이 존재하지 않는 깨끗한 무사고 상태입니다.\n")

        # 계산하기 대형 버튼
        calc_btn = tk.Button(root, text="💰 최종 진단평가가격 산출하기", command=self.run_final_evaluation, bg="#1E88E5", fg="white", font=("Arial", 11, "bold"), height=2)
        calc_btn.pack(fill=tk.X, padx=15, pady=10)

    def draw_car_vector(self):
        """Tkinter 내장 그래픽 함수로 평면 도해 그리기"""
        # 탑뷰 메인 바디 바운더리
        self.canvas.create_rectangle(50, 30, 620, 210, outline="#777", fill="#ffffff", width=2)
        
        # 각 파츠 드로잉
        self.canvas.create_rectangle(50, 80, 150, 160, outline="#333", fill="#e3f2fd", width=1.5)
        self.canvas.create_text(100, 120, text="후드\n(외판1)", font=("Arial", 9))

        self.canvas.create_rectangle(170, 30, 270, 90, outline="#333", fill="#e8f5e9", width=1.5)
        self.canvas.create_text(220, 60, text="앞도어(좌)", font=("Arial", 9))
        self.canvas.create_rectangle(170, 150, 270, 210, outline="#333", fill="#e8f5e9", width=1.5)
        self.canvas.create_text(220, 180, text="앞도어(우)", font=("Arial", 9))

        # 주요 골격 구조 (점선 처리)
        self.canvas.create_rectangle(60, 180, 180, 205, outline="#e53935", fill="#ffebee", width=1.5, dash=(4,2))
        self.canvas.create_text(120, 192, text="사이드멤버(좌)", fill="#cc1111", font=("Arial", 8))
        self.canvas.create_rectangle(60, 215, 180, 240, outline="#e53935", fill="#ffebee", width=1.5, dash=(4,2))
        self.canvas.create_text(120, 227, text="사이드멤버(우)", fill="#cc1111", font=("Arial", 8))

        self.canvas.create_rectangle(540, 80, 620, 160, outline="#333", fill="#fff3e0", width=1.5)
        self.canvas.create_text(580, 120, text="트렁크\n(외판1)", font=("Arial", 9))

    def on_diagram_click(self, event):
        x, y = event.x, event.y
        for part, info in self.regions.items():
            x1, y1, x2, y2 = info["box"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.popup_status_window(part, info["rank"])
                return

    def popup_status_window(self, part, rank):
        popup = tk.Toplevel(self.root)
        popup.title(f"📍 {part} 현황 매칭")
        popup.geometry("320x220")
        
        tk.Label(popup, text=f"선택 부위: {part} ({rank})", font=("Arial", 10, "bold")).pack(pady=10)
        status_var = tk.StringVar(value="정상")

        tk.Radiobutton(popup, text="정상 상태 (무감가)", variable=status_var, value="정상").pack(anchor=tk.W, padx=50)
        tk.Radiobutton(popup, text="이력: 교환(X)", variable=status_var, value="교환(X)").pack(anchor=tk.W, padx=50)
        tk.Radiobutton(popup, text="이력: 판금/용접(W)", variable=status_var, value="판금/용접(W)").pack(anchor=tk.W, padx=50)
        tk.Radiobutton(popup, text="요함: 도장 필요(P)", variable=status_var, value="도장필요(P)").pack(anchor=tk.W, padx=50)

        def save():
            res = status_var.get()
            if res == "정상":
                self.selected_damage.pop(part, None)
            else:
                self.selected_damage[part] = {"rank": rank, "status": res}
            self.refresh_status_box()
            popup.destroy()

        tk.Button(popup, text="확인 및 적용", command=save, bg="#43A047", fg="white", width=12).pack(pady=15)

    def refresh_status_box(self):
        self.status_box.delete("1.0", tk.END)
        if not self.selected_damage:
            self.status_box.insert(tk.END, "현재 감가 이력이 존재하지 않는 깨끗한 무사고 상태입니다.\n")
            return
        self.status_box.insert(tk.END, "📋 [현재 지정된 실시간 모색도 이력 현황]\n")
        for part, data in self.selected_damage.items():
            self.status_box.insert(tk.END, f"  • {part} ({data['rank']}) ──> 선택 상태: [{data['status']}]\n")

    def run_final_evaluation(self):
        """백엔드 연산 엔진과 프런트엔드 데이터 결합 연산 실행"""
        try:
            is_imp = True if self.origin_var.get() == "수입" else False
            disp = int(self.entry_disp.get())
            year = int(self.entry_year.get())
            mile = int(self.entry_mileage.get())
            base_p = int(self.entry_price.get())
        except ValueError:
            messagebox.showerror("입력 오류", "상단의 차량 스펙 데이터를 정확한 숫자로 입력하세요.")
            return

        # 1. 계산 엔진 객체 가동
        engine = CarEvaluator(is_import=is_imp, displacement=disp, reg_year=year, reg_month=1, mileage=mile, base_price_manwon=base_p)
        tier, tier_coef = engine.get_tier_and_coefficient()
        u_year, u_month, age_coef = engine.get_usage_period_and_coefficient()

        # 2. 실시간 모색도 UI 체크 데이터 바탕 감점 합산
        total_penalty_points = 0
        for part, data in self.selected_damage.items():
            rank = data["rank"]
            status = data["status"]
            
            # 기본 베이스 점수 파싱
            base_pt = self.rank_base_points.get(rank, 0)
            
            # 수리 형태에 따른 보정 산식 적용
            if status == "판금/용접(W)":
                base_pt = math.ceil(base_pt * 0.5) # 판금 용접은 50% 감점 적용
            elif status == "도장필요(P)":
                base_pt = 5 # 도장 필요 등 가벼운 수리필요는 일괄 5점 임시 배정
                
            total_penalty_points += base_pt

        # 3. 주행거리 표준치 비교 연산 연동
        std_mileage = int(u_month * 1.66 * 1000)
        mile_diff = std_mileage - mile
        mile_points = int(mile_diff / 1000)
        
        if mile_points < 0:
            total_penalty_points += abs(mile_points)

        # 4. 최종 정산 가격 연산
        penalty_amount = total_penalty_points  # 1점 = 1만원 규정
        final_price = base_p - penalty_amount
        if final_price < 0: final_price = 0

        # 결과 리포트 출력
        result_msg = (
            f"🎯 [최종 진단평가 판정 레포트]\n"
            f"──────────────────────────────────────────\n"
            f" 🚗 차량 등급 결과: {tier} 등급 (등급계수: {tier_coef})\n"
            f" 📅 사용 연수 결과: {u_year}년차 적용 (사용년 계수: {age_coef})\n"
            f" 🛣️ 주행거리 검증: 표준 {std_mileage:,}km VS 실제 {mile:,}km\n"
            f" 💥 상태도 감점합계: 총 {total_penalty_points} 점 감가 누적\n"
            f"──────────────────────────────────────────\n"
            f" 💰 입력 기준가격: {base_p:,} 만원\n"
            f" 📉 종합 감점금액: {penalty_amount:,} 만원\n"
            f" 🏁 최종 진단평가가격: {final_price:,} 만원"
        )
        messagebox.showinfo("📊 가치 산출 결과", result_msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = CarAssessmentApp(root)
    root.mainloop()