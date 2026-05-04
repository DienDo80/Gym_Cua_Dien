import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# ==========================================
# CẤU HÌNH KẾT NỐI
# ==========================================
URL = "https://kkdxkyoghdaneoblajng.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrZHhreW9naGRhbmVvYmxham5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc4NjkzODUsImV4cCI6MjA5MzQ0NTM4NX0.GmsHiN5F5KCnV5U0cjTa1adq2Mn371eORUCpPL44Ruw"

clean_url = URL.strip().replace('/rest/v1', '').rstrip('/')
clean_key = KEY.strip()

@st.cache_resource
def init_db() -> Client:
    return create_client(clean_url, clean_key)

try:
    supabase = init_db()
except Exception as e:
    st.error(f"🚨 LỖI KẾT NỐI: {e}")
    st.stop()

MUSCLE_CONFIG = {
    "Ngực": {"order": 1, "label": "CHEST", "min": 10, "max": 20},
    "Lưng": {"order": 2, "label": "BACK", "min": 10, "max": 20},
    "Đùi Trước": {"order": 3, "label": "QUADS", "min": 10, "max": 20},
    "Vai": {"order": 4, "label": "SHOULDER", "min": 8, "max": 16},
    "Tay Sau": {"order": 5, "label": "TRICEPS", "min": 6, "max": 12},
    "Tay Trước": {"order": 6, "label": "BICEPS", "min": 6, "max": 12},
    "Đùi Sau": {"order": 7, "label": "HAMSTRINGS", "min": 8, "max": 16},
    "Mông": {"order": 8, "label": "GLUTES", "min": 6, "max": 12},
    "Bắp Chân": {"order": 9, "label": "CALVES", "min": 6, "max": 12},
    "Bụng": {"order": 10, "label": "ABS", "min": 4, "max": 8}
}

def main():
    st.set_page_config(page_title="Eco Gym V25 - Manual Control", layout="wide")
    
    user_req = supabase.table("userprofile").select("*").eq("id", 1).execute()
    if not user_req.data:
        st.error("Chưa có dữ liệu User. Hãy đảm bảo bạn đã tạo bảng trên Supabase.")
        st.stop()
    u = user_req.data[0]
    
    st.sidebar.title("🧬 ECO GYM V25")
    menu = st.sidebar.selectbox("CHỌN MỤC TIÊU:", [
        "1. 📅 LỊCH TẬP LINH HOẠT", 
        "2. 🏋️ THÊM BÀI TẬP (THỦ CÔNG)", 
        "3. 🧘 CƠ CHẾ DELOAD", 
        "4. 📈 THỐNG KÊ & TĂNG TIẾN", 
        "5. 👤 CHỈ SỐ CƠ THỂ & CALO"
    ])

    # MỤC 1: LỊCH TẬP LINH HOẠT (DỜI LỊCH)
    if menu == "1. 📅 LỊCH TẬP LINH HOẠT":
        st.header("📅 Khung Lịch Tập Di Động")
        today_idx = datetime.datetime.today().weekday()
        cal = supabase.table("weeklycalendar").select("*").eq("owner_type", "me").order("day_index").execute().data
        
        for day in cal:
            idx, name, focus = day["day_index"], day["day_name"], day["focus"]
            with st.expander(f"{'📍' if idx == today_idx else '📅'} {name}: {focus}", expanded=(idx==today_idx)):
                # Dời lịch
                c_d1, c_d2 = st.columns([3, 1])
                new_day = c_d1.selectbox("Dời lịch sang:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], key=f"move_{idx}")
                if c_d2.button(f"🔄 Xác nhận dời", key=f"btn_move_{idx}"):
                    new_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(new_day)
                    supabase.table("workoutlog").update({"assigned_day": new_idx}).eq("assigned_day", idx).execute()
                    st.success(f"Đã dời toàn bộ bài tập sang {new_day}!")
                    st.rerun()

                st.markdown("---")
                exs = supabase.table("workoutlog").select("*").eq("assigned_day", idx).execute().data
                if exs:
                    # Lấy bài tập mới nhất, xếp Compound trước Isolation
                    df = pd.DataFrame(exs).sort_values(by=['id']).drop_duplicates('exercise', keep='last')
                    df = df.sort_values(by=['ex_type'], ascending=True) # Compound chữ C đứng trước Isolation chữ I
                    
                    for _, row in df.iterrows():
                        icon = "🔴" if "Compound" in str(row['ex_type']) else "🔵"
                        with st.form(key=f"f_{idx}_{row['exercise']}"):
                            st.write(f"{icon} **{row['exercise']}** - Nhóm cơ: {row['muscle_group']} | Phương pháp: {row['method']}")
                            c1, c2, c3 = st.columns(3)
                            nw = c1.number_input("Tạ (kg)", value=float(row['weight']), step=2.5)
                            nr = c2.number_input("Reps", value=int(row['reps']), step=1)
                            ns = c3.number_input("Sets", value=int(row['sets']), step=1)
                            if st.form_submit_button("✅ Lưu Kết Quả"):
                                supabase.table("workoutlog").insert({
                                    "owner_type": "me", "date": datetime.date.today().strftime("%Y-%m-%d"),
                                    "exercise": row['exercise'], "muscle_group": row['muscle_group'], 
                                    "weight": nw, "reps": nr, "sets": ns, 
                                    "rpe": row['rpe'], "rir": row['rir'], "method": row['method'],
                                    "assigned_day": idx, "ex_type": row['ex_type']
                                }).execute()
                                st.rerun()
                else:
                    st.info("Chưa có bài tập nào.")

    # MỤC 2: THÊM BÀI TẬP (KIỂM SOÁT THỦ CÔNG 100%)
    elif menu == "2. 🏋️ THÊM BÀI TẬP (THỦ CÔNG)":
        st.header("🏋️ Thiết Kế Chiêu Thức")
        st.caption("Nhập tên bài tập và tự tay phân bổ vào đúng nhóm cơ mục tiêu.")
        with st.form("add_ex"):
            name = st.text_input("Tên bài tập (VD: Incline Dumbbell Press):")
            mg = st.selectbox("Nhóm cơ tác động chính:", list(MUSCLE_CONFIG.keys()))
            method = st.selectbox("Phương pháp:", ["Standard", "TOPSET", "Back-off Set", "Rest-Pause", "Drop Set"])
            
            c1, c2, c3 = st.columns(3)
            rpe = c1.slider("RPE Target", 5.0, 10.0, 8.0, step=0.5)
            rir = c2.number_input("RIR Target", 0, 5, 1)
            typ = c3.selectbox("Loại", ["Compound", "Isolation"])
            
            day = st.selectbox("Gán vào thứ:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            
            if st.form_submit_button("Lưu Bài Tập"):
                if not name.strip():
                    st.error("⚠️ Đạo hữu vui lòng nhập tên bài tập!")
                else:
                    d_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(day)
                    supabase.table("workoutlog").insert({
                        "exercise": name.strip().title(), "muscle_group": mg, "method": method, "rpe": rpe, "rir": rir,
                        "ex_type": typ, "assigned_day": d_idx, "owner_type": "me", "sets": 2, "weight": 0, "reps": 0
                    }).execute()
                    st.success("Đã thêm chiêu thức vào giáo án!")

    # MỤC 3: CƠ CHẾ DELOAD
    elif menu == "3. 🧘 CƠ CHẾ DELOAD":
        st.header("🧘 Giao Thức Phục Hồi")
        curr_w, m_len = u["micro_week"], u["meso_length"]
        if curr_w > m_len:
            st.error(f"⚠️ CẢNH BÁO: ĐANG TRONG TUẦN DELOAD (Tuần {curr_w})")
            st.markdown("""
            **Nguyên tắc Deload:**
            * Giữ nguyên mức tạ (hoặc giảm 10-20%).
            * Cắt giảm 50% số Sets (Volume).
            * Dừng lại cách ngưỡng thất bại (Failure) 3-4 Reps (RIR 3-4).
            * Mục đích: Xả stress hệ thần kinh trung ương (CNS), chuẩn bị cho chu kỳ mới.
            """)
            if st.button("🏁 Kết thúc Deload -> Khởi động Meso Mới"):
                supabase.table("userprofile").update({"micro_week": 1}).eq("id", 1).execute()
                st.rerun()
        else:
            st.success(f"🔥 Tuần tập luyện: {curr_w}/{m_len}")
            st.info("Chưa đến lúc Deload. Hãy tiếp tục Progressive Overload!")
            if st.button("➡️ Chốt tuần & Tiến tới"):
                supabase.table("userprofile").update({"micro_week": curr_w + 1}).eq("id", 1).execute()
                st.rerun()

    # MỤC 4: THỐNG KÊ VOLUME & TĂNG TIẾN
    elif menu == "4. 📈 THỐNG KÊ & TĂNG TIẾN":
        st.header("📈 Kiểm Toán Volume & Tăng Tiến")
        logs = pd.DataFrame(supabase.table("workoutlog").select("*").execute().data)
        if not logs.empty:
            vol = logs.groupby('muscle_group')['sets'].sum().reset_index()
            for _, row in vol.iterrows():
                mg, s = row['muscle_group'], row['sets']
                cfg = MUSCLE_CONFIG.get(mg, {"min": 10, "max": 20})
                st.write(f"**{mg}**: {s} sets/tuần")
                if s < cfg["min"]: st.warning(f"⚠️ Thiếu volume (Cần ít nhất {cfg['min']} sets)")
                elif s > cfg["max"]: st.error(f"🚨 Quá tải (Nhiều hơn {cfg['max']} sets)")
                else: st.success("✅ Volume tối ưu (Nằm trong khoảng 10-20 sets)")
                st.progress(min(s/cfg["max"], 1.0))
            
            st.markdown("---")
            st.subheader("Theo dõi mức tạ (Mới nhất)")
            st.dataframe(logs[['date', 'exercise', 'weight', 'reps', 'sets', 'rpe']].sort_values('date', ascending=False).head(15))

    # MỤC 5: CHỈ SỐ CƠ THỂ & CALO (NHẬP THỦ CÔNG)
    elif menu == "5. 👤 CHỈ SỐ CƠ THỂ & CALO":
        st.header("👤 Hồ Sơ Cá Nhân & Dinh Dưỡng")
        
        with st.expander("📚 BẢNG CÔNG THỨC THAM KHẢO (Bấm để xem)"):
            st.markdown("""
            **1. Công thức TDEE thực chiến:**
            `TDEE = Cân nặng (kg) x Hệ số vận động`
            * Hệ số 30: Ít vận động, ngồi văn phòng
            * Hệ số 33-35: Tập luyện 3-5 buổi/tuần
            * Hệ số 40-45: Vận động nặng, lao động chân tay hoặc tập cực nặng
            
            **2. Công thức BMI:**
            `BMI = Cân nặng (kg) / (Chiều cao (m) x Chiều cao (m))`
            
            **3. Nguyên tắc Thâm thụt/Thặng dư Calo:**
            * **Cutting (Giảm mỡ):** TDEE - (300 đến 500 kcal)
            * **Mini-cutting:** TDEE - (500 đến 700 kcal)
            * **Bulking (Tăng cơ):** TDEE + (200 đến 300 kcal)
            * **Recomposition (Tăng cơ giảm mỡ):** Ăn bằng TDEE hoặc thâm thụt nhẹ (100-200 kcal), giữ Protein cao.
            """)

        with st.form("body_info_manual"):
            st.subheader("✍️ BẢNG NHẬP CHỈ SỐ THỦ CÔNG")
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Chiều cao (cm)", value=float(u.get('height', 178.0)))
            w = c2.number_input("Cân nặng (kg)", value=float(u.get('weight', 90.0)))
            bf = c3.number_input("Tỷ lệ mỡ - Body Fat (%)", value=float(u.get('body_fat', 24.0) or 24.0))
            
            st.markdown("---")
            c4, c5 = st.columns(2)
            goal = c4.selectbox("Phương pháp đang áp dụng:", 
                                ["Cutting (Giảm mỡ)", "Mini-cutting", "Bulking (Tăng cơ)", "Recomposition (Tăng cơ giảm mỡ)"], 
                                index=0)
            
            manual_tdee = c5.number_input("TDEE bạn tự tính (kcal)", value=int(u.get('tdee_method', 2500) or 2500), step=50)
            target_cal = st.number_input("Mục tiêu Calo nạp vào hàng ngày (kcal)", value=int(u.get('daily_calories', 2200) or 2200), step=50)

            if st.form_submit_button("💾 Lưu Trữ Dữ Liệu"):
                supabase.table("userprofile").update({
                    "height": h, "weight": w, "body_fat": bf,
                    "goal_type": goal, "tdee_method": str(manual_tdee), "daily_calories": target_cal
                }).eq("id", 1).execute()
                st.success("Đã ghi nhận các chỉ số cơ thể do bạn thiết lập!")
                
        st.markdown("---")
        st.subheader("🎯 TÓM TẮT MỤC TIÊU HIỆN TẠI")
        col1, col2, col3 = st.columns(3)
        col1.metric("Cân nặng / Body Fat", f"{u.get('weight')} kg", f"{u.get('body_fat')}%")
        col2.metric("TDEE", f"{u.get('tdee_method')} kcal")
        col3.metric("Mục tiêu nạp vào", f"{u.get('daily_calories')} kcal", goal.split(' ')[0])

if __name__ == "__main__":
    main()