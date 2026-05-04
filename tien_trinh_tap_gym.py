import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ==========================================
# PHẦN 1: TÂM PHÁP CHUYÊN SÂU (DATABASE)
# ==========================================
class DBManager:
    def __init__(self, db_name="eco_gym_pro_v7.db"): 
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.upgrade_database()
        self.init_user()
        self.init_calendar()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS UserProfile 
            (id INTEGER PRIMARY KEY, height REAL, weight REAL, target_weight REAL, 
             activity_multiplier REAL, protein_multiplier REAL, fat_multiplier REAL,
             micro_week INTEGER, meso_phase INTEGER, meso_goal TEXT, macro_goal TEXT,
             diet_phase TEXT, calorie_offset INTEGER, buddy_name TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS WorkoutLog 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_type TEXT, date TEXT, exercise TEXT, muscle_group TEXT, 
             weight REAL, reps INTEGER, sets INTEGER, rpe REAL, rir REAL, method TEXT, assigned_day INTEGER, one_rm REAL)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS WeeklyCalendar 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_type TEXT, day_index INTEGER, day_name TEXT, focus TEXT)''')
        self.conn.commit()

    def upgrade_database(self):
        try: self.cursor.execute("ALTER TABLE UserProfile ADD COLUMN micro_goal TEXT DEFAULT 'Tập trung form'")
        except: pass
        try: self.cursor.execute("ALTER TABLE UserProfile ADD COLUMN vol_level TEXT DEFAULT 'Thấp'")
        except: pass
        try: self.cursor.execute("ALTER TABLE UserProfile ADD COLUMN int_level TEXT DEFAULT 'Cao'")
        except: pass
        try: self.cursor.execute("ALTER TABLE UserProfile ADD COLUMN freq_level TEXT DEFAULT 'Cao'")
        except: pass
        try: self.cursor.execute("ALTER TABLE UserProfile ADD COLUMN meso_length INTEGER DEFAULT 6")
        except: pass
        
        # Thêm cột phân loại chiêu thức (Compound/Isolation)
        try: self.cursor.execute("ALTER TABLE WorkoutLog ADD COLUMN ex_type TEXT DEFAULT 'Compound (Đa khớp)'")
        except: pass
        
        self.conn.commit()

    def init_user(self):
        self.cursor.execute("SELECT * FROM UserProfile WHERE id=1")
        if not self.cursor.fetchone():
            self.cursor.execute('''INSERT INTO UserProfile 
                (id, height, weight, target_weight, activity_multiplier, protein_multiplier, fat_multiplier, 
                 micro_week, meso_phase, meso_goal, macro_goal, diet_phase, calorie_offset, buddy_name) 
                VALUES 
                (1, 178.0, 90.0, 80.0, 33.0, 2.2, 0.8, 1, 1, "Hypertrophy (Tăng cơ)", "Xây nền tảng", 
                "Recomposition", -300, "Bạn Đồng Tu")''')
            self.conn.commit()

    def init_calendar(self):
        self.cursor.execute("SELECT COUNT(*) FROM WeeklyCalendar")
        if self.cursor.fetchone()[0] == 0:
            days = [(0, "Thứ 2", "Ngực / Vai / Tay Sau"), (1, "Thứ 3", "Lưng / Tay Trước"), 
                    (2, "Thứ 4", "Nghỉ Ngơi"), (3, "Thứ 5", "Đùi / Mông / Bắp Chân"), 
                    (4, "Thứ 6", "Ngực / Lưng (Upper)"), (5, "Thứ 7", "Chân (Lower)"), (6, "Chủ Nhật", "Nghỉ Ngơi")]
            for idx, name, focus in days:
                self.cursor.execute("INSERT INTO WeeklyCalendar (owner_type, day_index, day_name, focus) VALUES (?, ?, ?, ?)", ("me", idx, name, focus))
            for idx, name, focus in days:
                self.cursor.execute("INSERT INTO WeeklyCalendar (owner_type, day_index, day_name, focus) VALUES (?, ?, ?, ?)", ("buddy", idx, name, focus))
            self.conn.commit()

@st.cache_resource
def get_db():
    return DBManager()

db = get_db()

# ==========================================
# CƠ CHẾ ĐỘNG & GIAO THỨC DELOAD / POST-DELOAD
# ==========================================
def get_dynamic_guidance(meso_goal, v, i, f, micro_week, meso_length):
    if micro_week > meso_length:
        warn = f"🧘 ĐANG TRONG TUẦN DELOAD: Phục hồi hệ thần kinh và khớp."
        if "Hypertrophy" in meso_goal:
            return {"reps": "6-12", "sets": "1 (Giảm 50% Volume)", "rir": "3-4", "rpe": "6.0-7.0", 
                    "warn": warn, "desc": "DELOAD TĂNG CƠ: Giảm 30-50% khối lượng Set tập. Giữ nguyên tạ để giữ cơ, KHÔNG tập đến thất bại."}
        else: 
            return {"reps": "3-5", "sets": "Giữ nguyên", "rir": "4-5", "rpe": "5.0-6.0", 
                    "warn": warn, "desc": "DELOAD SỨC MẠNH: Giảm 30-50% mức Tạ (Intensity). Giữ nguyên số set để duy trì cảm giác form."}

    if "Strength" in meso_goal: reps = "1-5"
    elif "Peaking" in meso_goal: reps = "1-3"
    else: reps = "6-12" 
    
    if i == "Cao": rir, rpe = "0-1", "9.0-10.0"
    elif i == "Vừa": rir, rpe = "1-2", "8.0-9.0"
    else: rir, rpe = "2-3", "7.0-8.0"

    if micro_week == 1:
        if v == "Cao": sets = "2-3 (MEV)"
        elif v == "Vừa": sets = "1-2 (MEV)"
        else: sets = "1 (MEV)"
        desc = "🚀 TUẦN 1 (TẠO ĐÀ): Hệ thống đã TỰ ĐỘNG GIẢM VOLUME (Sets) về mức MEV. Hãy giữ tạ nặng nhưng tập ít Set lại để tạo đà bứt phá."
    else:
        if v == "Cao": sets = "3-5"
        elif v == "Vừa": sets = "2-3"
        else: sets = "1-2"
        desc = "🔥 Bám sát thông số. Nỗ lực phá vỡ kỷ lục tuần trước (Progressive Overload). Lùi 1 bước nếu thấy quá tải."
        
    score = (3 if v=="Cao" else 2 if v=="Vừa" else 1) + (3 if i=="Cao" else 2 if i=="Vừa" else 1) + (3 if f=="Cao" else 2 if f=="Vừa" else 1)
    if score >= 8: warn = "⚠️ RED-ZONE: V-I-F đều chạm nóc! Nguy cơ chấn thương cao."
    elif score == 7: warn = "⚡ CAM: Ngưỡng tới hạn. Yêu cầu phục hồi tốt."
    else: warn = "✅ TỐI ƯU: Tam giác cân bằng."
        
    return {"reps": reps, "sets": sets, "rir": rir, "rpe": rpe, "warn": warn, "desc": desc}

# ==========================================
# PHẦN 2: GIAO DIỆN APP
# ==========================================
def main():
    st.set_page_config(page_title="Eco Gym V18 - Combat Layout", page_icon="🧬", layout="wide")
    
    db.cursor.execute("SELECT buddy_name, meso_goal, vol_level, int_level, freq_level, micro_week, meso_length FROM UserProfile WHERE id=1")
    user_data = db.cursor.fetchone()
    if user_data and len(user_data) == 7:
        buddy_name, current_goal, v_lvl, i_lvl, f_lvl, current_week, meso_length = user_data
    else:
        buddy_name, current_goal, v_lvl, i_lvl, f_lvl, current_week, meso_length = "Bạn", "Hypertrophy", "Thấp", "Cao", "Cao", 1, 6
        
    guide = get_dynamic_guidance(current_goal, v_lvl, i_lvl, f_lvl, current_week, meso_length)
    
    st.sidebar.title("🧬 ECO GYM V18")
    st.sidebar.markdown("---")
    selected_name = st.sidebar.radio("👥 Đang huấn luyện cho:", ["Tôi", buddy_name], horizontal=True)
    owner_type = "me" if selected_name == "Tôi" else "buddy"
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Chuyển đến:", ["📅 Tác Chiến Hàng Ngày", "🏋️ Lưu Chiêu Thức Mới", "📈 Bản Đồ Chiến Lược", "⚙️ Tam Giác & Dinh Dưỡng"])

    if menu == "📅 Tác Chiến Hàng Ngày":
        st.header(f"📅 Lịch Tác Chiến của: {selected_name}")
        
        st.markdown("### 🔋 Chỉ Số Sẵn Sàng")
        readiness = st.slider("Chất lượng giấc ngủ & Căng thẳng hôm nay (1-10):", 1, 10, 8)
        if readiness <= 5:
            st.error("⚠️ THỂ TRẠNG YẾU: Cắt giảm Volume hoặc hạ RPE để bảo vệ hệ thần kinh.")
        elif readiness >= 8:
            st.success("🔥 THỂ TRẠNG ĐỈNH: Sẵn sàng công phá kỷ lục!")

        st.markdown("---")
        
        if current_week == 1:
            st.success(f"**{guide['desc']}**")
            st.info(f"👉 **Thông số Yêu cầu:** {guide['sets']} Working Sets | {guide['reps']} Reps | RIR {guide['rir']} | RPE {guide['rpe']}")
        elif current_week > meso_length:
            st.warning(f"**Trạng thái Deload:** {guide['desc']}")
        else:
            st.info(f"👉 **Kim chỉ nam Tuần {current_week}:** {guide['sets']} Working Sets | {guide['reps']} Reps | RIR {guide['rir']} | RPE {guide['rpe']}")
        
        today_idx = datetime.datetime.today().weekday()
        db.cursor.execute("SELECT day_index, day_name, focus FROM WeeklyCalendar WHERE owner_type=? ORDER BY day_index", (owner_type,))
        cal_data = db.cursor.fetchall()

        for day in cal_data:
            idx, name, focus = day
            is_today = (idx == today_idx)
            icon = "📍" if is_today else "📅"
            is_rest_day = "nghỉ" in focus.lower()
            
            with st.expander(f"{icon} {name} - Mục tiêu: {focus}", expanded=is_today):
                col_f1, col_f2 = st.columns([3, 1])
                new_focus = col_f1.text_input("Sửa mục tiêu:", value=focus, key=f"f_{owner_type}_{idx}")
                if col_f2.button("Lưu", key=f"b_{owner_type}_{idx}"):
                    db.cursor.execute("UPDATE WeeklyCalendar SET focus=? WHERE owner_type=? AND day_index=?", (new_focus, owner_type, idx))
                    db.conn.commit()
                    st.rerun()
                
                st.markdown("---")
                if not is_rest_day:
                    # Lấy danh sách kèm theo ex_type
                    db.cursor.execute("""
                        SELECT exercise, muscle_group, weight, reps, sets, rpe, rir, method, ex_type 
                        FROM WorkoutLog 
                        WHERE owner_type=? AND assigned_day=? 
                        GROUP BY exercise HAVING MAX(date)
                    """, (owner_type, idx))
                    exercises = db.cursor.fetchall()
                    
                    if exercises:
                        # Tách bài tập thành 2 nhóm rõ rệt
                        compounds = [ex for ex in exercises if ex[8] is None or "Compound" in str(ex[8])]
                        isolations = [ex for ex in exercises if ex[8] is not None and "Isolation" in str(ex[8])]

                        # HÀM RENDER FORM NHẬP LIỆU (Tối ưu UI)
                        def render_exercise_card(ex, ex_category_icon):
                            ex_name, ex_mus, ex_w, ex_r, ex_s, ex_rpe, ex_rir, ex_meth, ex_type_val = ex
                            suggest_sets = int(ex_s)
                            if current_week == 1 and ex_s > 1:
                                suggest_sets = max(1, int(ex_s) - 1)
                            
                            # Tên bài tập nổi bật
                            if current_week == 1 and suggest_sets < int(ex_s):
                                ex_title = f"{ex_category_icon} {ex_name} (📉 Giảm còn {suggest_sets} Set)"
                            else:
                                ex_title = f"{ex_category_icon} {ex_name} (Kỷ lục: {ex_w}kg x {ex_r} reps)"
                                
                            with st.expander(ex_title):
                                with st.form(key=f"qf_{owner_type}_{idx}_{ex_name}", clear_on_submit=False):
                                    c1, c2, c3, c4, c5 = st.columns(5)
                                    nw = c1.number_input("Tạ (kg)", value=float(ex_w), step=2.5)
                                    nr = c2.number_input("Reps", value=int(ex_r), step=1)
                                    ns = c3.number_input("Working Sets", value=suggest_sets, step=1)
                                    nrpe = c4.number_input("RPE", value=float(ex_rpe), step=0.5)
                                    nrir = c5.number_input("RIR", value=int(ex_rir), step=1)
                                    
                                    col_btn1, col_btn2 = st.columns([2, 1])
                                    if col_btn1.form_submit_button("✅ Lưu Set Tập"):
                                        today_str = datetime.date.today().strftime("%Y-%m-%d")
                                        n_1rm = nw * (1 + nr/30) if nr > 1 else nw
                                        db.cursor.execute("""INSERT INTO WorkoutLog 
                                            (owner_type, date, exercise, muscle_group, weight, reps, sets, rpe, rir, method, assigned_day, one_rm, ex_type) 
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                                            (owner_type, today_str, ex_name, ex_mus, nw, nr, ns, nrpe, nrir, ex_meth, idx, n_1rm, ex_type_val))
                                        db.conn.commit()
                                        st.success(f"Đã cập nhật {ex_name}!")
                                        st.rerun()
                                        
                                    if col_btn2.form_submit_button("❌ Bỏ bài này khỏi lịch"):
                                        db.cursor.execute("UPDATE WorkoutLog SET assigned_day=99 WHERE owner_type=? AND exercise=? AND assigned_day=?", (owner_type, ex_name, idx))
                                        db.conn.commit()
                                        st.rerun()

                        # KHU VỰC BÀI ĐA KHỚP
                        if compounds:
                            st.markdown("#### 🔴 BÀI TẬP ĐA KHỚP (Ưu tiên tập trước)")
                            for ex in compounds:
                                render_exercise_card(ex, "🔴")

                        # KHU VỰC BÀI CÔ LẬP
                        if isolations:
                            st.markdown("#### 🔵 BÀI TẬP CÔ LẬP (Tập sau để bơm máu)")
                            for ex in isolations:
                                render_exercise_card(ex, "🔵")
                                
                    else:
                        st.info("Chưa có bài tập nào. Hãy qua Tab 'Lưu Chiêu Thức Mới' để bổ sung.")

    elif menu == "🏋️ Lưu Chiêu Thức Mới":
        st.header(f"📝 Bổ Sung Vũ Khí Cho: {selected_name}")
        st.info(f"**Target:** {guide['sets']} Sets | {guide['reps']} Reps | RIR {guide['rir']}")
        
        days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        today_idx = datetime.datetime.today().weekday()
        
        with st.form("workout_log"):
            col1, col2, col3 = st.columns(3)
            ex_name = col1.text_input("Tên bài tập")
            muscle = col2.selectbox("Nhóm cơ", ["Ngực", "Lưng", "Đùi Trước", "Đùi Sau", "Vai", "Tay Trước", "Tay Sau", "Bắp Chân"])
            ex_type = col3.selectbox("Phân Loại", ["Compound (Đa khớp)", "Isolation (Cô lập)"])
            
            c1, c2, c3 = st.columns(3)
            w = c1.number_input("Mức tạ (kg)", step=2.5)
            r = c2.number_input("Số Reps", step=1)
            s = c3.number_input("Working Sets", step=1, value=1)
            
            c4, c5, c6 = st.columns(3)
            rpe = c4.slider("RPE", 1.0, 10.0, 8.5, step=0.5)
            rir = c5.slider("RIR", 0, 5, 1, step=1)
            method = c6.selectbox("Phương pháp", ["Standard", "Top Set / Back-off Set", "Rest-Pause", "Drop Set"])
            
            target_day = st.selectbox("Gán vào thứ:", days_vn, index=today_idx)
            if st.form_submit_button("Lưu & Phân Bổ"):
                if ex_name:
                    day_idx = days_vn.index(target_day)
                    one_rm = w * (1 + r/30) if r > 1 else w
                    today = datetime.date.today().strftime("%Y-%m-%d")
                    db.cursor.execute("""INSERT INTO WorkoutLog 
                        (owner_type, date, exercise, muscle_group, weight, reps, sets, rpe, rir, method, assigned_day, one_rm, ex_type) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                        (owner_type, today, ex_name.title(), muscle, w, r, s, rpe, rir, method, day_idx, one_rm, ex_type))
                    db.conn.commit()
                    st.success("Đã phân bổ chiêu thức thành công!")

    elif menu == "📈 Bản Đồ Chiến Lược (Chu Kỳ)":
        st.header(f"📊 Chiến Lược Gia Cơ Bắp - {selected_name}")
        db.cursor.execute("SELECT macro_goal FROM UserProfile WHERE id=1")
        macro_goal = db.cursor.fetchone()[0]
        
        with st.container():
            st.markdown("### 🌍 TẦNG 1: MACROCYCLE (Tầm nhìn Vĩ mô)")
            with st.form("macro_form"):
                new_macro = st.text_input("Định hình chiến lược dài hạn:", value=macro_goal)
                if st.form_submit_button("Lưu Macrocycle"):
                    db.cursor.execute("UPDATE UserProfile SET macro_goal=? WHERE id=1", (new_macro,))
                    db.conn.commit()
                    st.rerun()

        st.markdown("---")
        with st.container():
            st.markdown(f"### 🛡️ TẦNG 2: MESOCYCLE (Chiến dịch Trọng điểm)")
            c1, c2 = st.columns(2)
            c1.metric("Mục tiêu hiện tại:", current_goal)
            with c2.expander("Sửa đổi độ dài chiến dịch"):
                with st.form("meso_len_form"):
                    new_len = st.selectbox("Độ dài Giai đoạn này (Tuần):", [4, 6, 8, 12], index=[4, 6, 8, 12].index(meso_length))
                    if st.form_submit_button("Cập nhật"):
                        db.cursor.execute("UPDATE UserProfile SET meso_length=? WHERE id=1", (new_len,))
                        db.conn.commit()
                        st.rerun()

        st.markdown("---")
        with st.container():
            if current_week > meso_length:
                st.error(f"🛑 ĐÃ CHẠM NGƯỠNG TUẦN {current_week}. KÍCH HOẠT GIAO THỨC DELOAD!")
            elif current_week == 1:
                st.success("🚀 ĐANG Ở TUẦN 1 (MEV): Ứng dụng đã tự động giảm Volume. Hãy tập trung vào chất lượng kỹ thuật!")
            else:
                st.markdown(f"### ⚔️ TẦNG 3: MICROCYCLE (Tác chiến Tuần {current_week} / {meso_length})")
                
            st.progress(min(current_week / (meso_length + 1), 1.0))
            
            if current_week <= meso_length:
                if st.button("▶️ Chốt Tuần. Tiến sang Tuần Tiếp Theo"):
                    db.cursor.execute("UPDATE UserProfile SET micro_week=? WHERE id=1", (current_week + 1,))
                    db.conn.commit()
                    st.rerun()
            
            if current_week > meso_length:
                with st.form("deload_finish_form"):
                    next_goal = st.selectbox("Mục tiêu chiến dịch tới:", ["Hypertrophy (Tăng cơ)", "Strength (Sức mạnh)"])
                    if st.form_submit_button("Hoàn thành Deload & Bắt đầu Chiến Dịch Mới"):
                        db.cursor.execute("UPDATE UserProfile SET micro_week=1, meso_phase=meso_phase+1, meso_goal=? WHERE id=1", (next_goal,))
                        db.conn.commit()
                        st.rerun()

    elif menu == "⚙️ Tam Giác & Dinh Dưỡng":
        st.header("⚙️ Cấu Hình Cốt Lõi")
        with st.expander("🔺 Tùy Chỉnh Tam Giác Huấn Luyện", expanded=True):
            with st.form("triad_form"):
                c1, c2, c3 = st.columns(3)
                new_v = c1.selectbox("Khối lượng (Volume)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(v_lvl))
                new_i = c2.selectbox("Cường độ (Intensity)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(i_lvl))
                new_f = c3.selectbox("Tần suất (Frequency)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(f_lvl))
                if st.form_submit_button("Cập Nhật Gen Huấn Luyện"):
                    db.cursor.execute("UPDATE UserProfile SET vol_level=?, int_level=?, freq_level=? WHERE id=1", (new_v, new_i, new_f))
                    db.conn.commit()
                    st.rerun()
            st.info(guide['warn'])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Lỗi: {e}")