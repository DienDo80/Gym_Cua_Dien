import streamlit as st
from supabase import create_client, Client
import datetime

# ==========================================
# THAY 2 DÒNG NÀY BẰNG BẢO BỐI CỦA BẠN
# ==========================================
SUPABASE_URL = "https://kkdxkyoghdaneoblajng.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrZHhreW9naGRhbmVvYmxham5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc4NjkzODUsImV4cCI6MjA5MzQ0NTM4NX0.GmsHiN5F5KCnV5U0cjTa1adq2Mn371eORUCpPL44Ruw"

@st.cache_resource
def init_db() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_db()
except Exception as e:
    st.error(f"🚨 LỖI KHỞI TẠO KẾT NỐI: {e}")
    st.stop()

# KHỞI TẠO DỮ LIỆU ĐÁM MÂY LẦN ĐẦU (Đã sửa chữ thường)
def init_data():
    user = supabase.table("userprofile").select("id").eq("id", 1).execute()
    if not user.data:
        supabase.table("userprofile").insert({
            "id": 1, "height": 178.0, "weight": 90.0, "target_weight": 80.0,
            "activity_multiplier": 33.0, "protein_multiplier": 2.2, "fat_multiplier": 0.8,
            "micro_week": 1, "meso_phase": 1, "meso_goal": "Hypertrophy (Tăng cơ)",
            "macro_goal": "Xây nền tảng", "diet_phase": "Recomposition",
            "calorie_offset": -300, "buddy_name": "Bạn Đồng Tu",
            "micro_goal": "Tập trung form", "vol_level": "Thấp", "int_level": "Cao", "freq_level": "Cao", "meso_length": 6
        }).execute()

    cal = supabase.table("weeklycalendar").select("id").execute()
    if not cal.data:
        days = [(0, "Thứ 2", "Ngực / Vai / Tay Sau"), (1, "Thứ 3", "Lưng / Tay Trước"), 
                (2, "Thứ 4", "Nghỉ Ngơi"), (3, "Thứ 5", "Đùi / Mông / Bắp Chân"), 
                (4, "Thứ 6", "Ngực / Lưng (Upper)"), (5, "Thứ 7", "Chân (Lower)"), (6, "Chủ Nhật", "Nghỉ Ngơi")]
        for o in ["me", "buddy"]:
            for idx, name, focus in days:
                supabase.table("weeklycalendar").insert({"owner_type": o, "day_index": idx, "day_name": name, "focus": focus}).execute()

try:
    init_data()
except Exception as e:
    st.error(f"🚨 Lỗi khởi tạo: {e}")
    st.stop()

# KIM CHỈ NAM ĐỘNG
def get_dynamic_guidance(meso_goal, v, i, f, micro_week, meso_length):
    if micro_week > meso_length:
        warn = f"🧘 ĐANG TRONG TUẦN DELOAD: Phục hồi hệ thần kinh và khớp."
        if "Hypertrophy" in meso_goal:
            return {"reps": "6-12", "sets": "1", "rir": "3-4", "rpe": "6.0", "warn": warn, "desc": "DELOAD: Giữ tạ, giảm set."}
        else: 
            return {"reps": "3-5", "sets": "Giữ nguyên", "rir": "4-5", "rpe": "5.0", "warn": warn, "desc": "DELOAD: Giảm tạ, giữ set."}

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
        desc = "🚀 TUẦN 1 (TẠO ĐÀ): Hệ thống đã TỰ GIẢM VOLUME (Sets) về mức tối thiểu."
    else:
        if v == "Cao": sets = "3-5"
        elif v == "Vừa": sets = "2-3"
        else: sets = "1-2"
        desc = "🔥 Bám sát thông số. Nỗ lực phá vỡ kỷ lục tuần trước (Progressive Overload)."
        
    return {"reps": reps, "sets": sets, "rir": rir, "rpe": rpe, "warn": "", "desc": desc}

# GIAO DIỆN
def main():
    st.set_page_config(page_title="Eco Gym V19 - Cloud Edition", page_icon="☁️", layout="wide")
    
    user_res = supabase.table("userprofile").select("*").eq("id", 1).execute()
    if not user_res.data: return
    u = user_res.data[0]
    
    buddy_name, current_goal = u.get("buddy_name"), u.get("meso_goal")
    v_lvl, i_lvl, f_lvl = u.get("vol_level"), u.get("int_level"), u.get("freq_level")
    current_week, meso_length = u.get("micro_week"), u.get("meso_length")
    
    guide = get_dynamic_guidance(current_goal, v_lvl, i_lvl, f_lvl, current_week, meso_length)
    
    st.sidebar.title("☁️ ECO GYM V19")
    selected_name = st.sidebar.radio("👥 Huấn luyện cho:", ["Tôi", buddy_name], horizontal=True)
    owner_type = "me" if selected_name == "Tôi" else "buddy"
    menu = st.sidebar.radio("Chuyển đến:", ["📅 Tác Chiến Hàng Ngày", "🏋️ Lưu Chiêu Thức Mới", "📈 Bản Đồ Chiến Lược", "⚙️ Tam Giác"])

    if menu == "📅 Tác Chiến Hàng Ngày":
        st.header(f"📅 Lịch Tác Chiến: {selected_name}")
        st.info(f"👉 **Kim chỉ nam Tuần {current_week}:** {guide['sets']} Sets | {guide['reps']} Reps | RIR {guide['rir']}")
        
        today_idx = datetime.datetime.today().weekday()
        cal_res = supabase.table("weeklycalendar").select("*").eq("owner_type", owner_type).order("day_index").execute()
        
        for day in cal_res.data:
            idx, name, focus = day["day_index"], day["day_name"], day["focus"]
            is_today = (idx == today_idx)
            icon = "📍" if is_today else "📅"
            
            with st.expander(f"{icon} {name} - Mục tiêu: {focus}", expanded=is_today):
                c_f1, c_f2 = st.columns([3, 1])
                new_focus = c_f1.text_input("Sửa mục tiêu:", value=focus, key=f"f_{idx}")
                if c_f2.button("Lưu", key=f"b_{idx}"):
                    supabase.table("weeklycalendar").update({"focus": new_focus}).eq("owner_type", owner_type).eq("day_index", idx).execute()
                    st.rerun()
                
                st.markdown("---")
                if "nghỉ" not in focus.lower():
                    ex_res = supabase.table("workoutlog").select("*").eq("owner_type", owner_type).eq("assigned_day", idx).execute()
                    
                    exercises = []
                    seen_ex = set()
                    sorted_ex = sorted(ex_res.data, key=lambda x: x["id"], reverse=True)
                    for ex in sorted_ex:
                        if ex["exercise"] not in seen_ex:
                            exercises.append(ex)
                            seen_ex.add(ex["exercise"])
                            
                    if exercises:
                        compounds = [e for e in exercises if not e.get("ex_type") or "Compound" in e.get("ex_type")]
                        isolations = [e for e in exercises if e.get("ex_type") and "Isolation" in e.get("ex_type")]

                        def render_exercise_card(ex, icon_sym):
                            ex_name, ex_w, ex_r, ex_s = ex["exercise"], ex["weight"], ex["reps"], ex["sets"]
                            ex_rpe, ex_rir, ex_meth, ex_mus = ex["rpe"], ex["rir"], ex["method"], ex["muscle_group"]
                            ex_type_val = ex.get("ex_type", "Compound (Đa khớp)")
                            
                            suggest_sets = int(ex_s)
                            if current_week == 1 and ex_s > 1:
                                suggest_sets = max(1, int(ex_s) - 1)
                                ex_title = f"{icon_sym} {ex_name} (📉 Giảm còn {suggest_sets} Set)"
                            else:
                                ex_title = f"{icon_sym} {ex_name} (Kỷ lục: {ex_w}kg x {ex_r} reps)"
                                
                            with st.expander(ex_title):
                                with st.form(key=f"qf_{idx}_{ex_name}", clear_on_submit=False):
                                    c1, c2, c3, c4, c5 = st.columns(5)
                                    nw = c1.number_input("Tạ (kg)", value=float(ex_w), step=2.5)
                                    nr = c2.number_input("Reps", value=int(ex_r), step=1)
                                    ns = c3.number_input("Sets", value=suggest_sets, step=1)
                                    nrpe = c4.number_input("RPE", value=float(ex_rpe), step=0.5)
                                    nrir = c5.number_input("RIR", value=int(ex_rir), step=1)
                                    
                                    cb1, cb2 = st.columns([2, 1])
                                    if cb1.form_submit_button("✅ Lưu Set"):
                                        n_1rm = nw * (1 + nr/30) if nr > 1 else nw
                                        today_str = datetime.date.today().strftime("%Y-%m-%d")
                                        supabase.table("workoutlog").insert({
                                            "owner_type": owner_type, "date": today_str, "exercise": ex_name,
                                            "muscle_group": ex_mus, "weight": nw, "reps": nr, "sets": ns,
                                            "rpe": nrpe, "rir": nrir, "method": ex_meth, "assigned_day": idx,
                                            "one_rm": n_1rm, "ex_type": ex_type_val
                                        }).execute()
                                        st.rerun()
                                    if cb2.form_submit_button("❌ Bỏ bài"):
                                        supabase.table("workoutlog").update({"assigned_day": 99}).eq("owner_type", owner_type).eq("exercise", ex_name).eq("assigned_day", idx).execute()
                                        st.rerun()

                        if compounds:
                            st.markdown("#### 🔴 BÀI TẬP ĐA KHỚP")
                            for ex in compounds: render_exercise_card(ex, "🔴")
                        if isolations:
                            st.markdown("#### 🔵 BÀI TẬP CÔ LẬP")
                            for ex in isolations: render_exercise_card(ex, "🔵")
                    else:
                        st.info("Chưa có bài tập nào.")

    elif menu == "🏋️ Lưu Chiêu Thức Mới":
        st.header("📝 Bổ Sung Vũ Khí")
        days_vn = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        with st.form("workout_log"):
            co1, co2, co3 = st.columns(3)
            ex_name = co1.text_input("Tên bài tập")
            muscle = co2.selectbox("Nhóm cơ", ["Ngực", "Lưng", "Đùi Trước", "Đùi Sau", "Vai", "Tay Trước", "Tay Sau", "Bắp Chân"])
            ex_type = co3.selectbox("Phân Loại", ["Compound (Đa khớp)", "Isolation (Cô lập)"])
            
            c1, c2, c3 = st.columns(3)
            w = c1.number_input("Mức tạ (kg)", step=2.5)
            r = c2.number_input("Số Reps", step=1)
            s = c3.number_input("Working Sets", step=1, value=1)
            
            c4, c5, c6 = st.columns(3)
            rpe = c4.slider("RPE", 1.0, 10.0, 8.5, step=0.5)
            rir = c5.slider("RIR", 0, 5, 1, step=1)
            method = c6.selectbox("Phương pháp", ["Standard", "Top Set", "Rest-Pause", "Drop Set"])
            
            target_day = st.selectbox("Gán vào thứ:", days_vn, index=datetime.datetime.today().weekday())
            if st.form_submit_button("Lưu & Phân Bổ"):
                if ex_name:
                    one_rm = w * (1 + r/30) if r > 1 else w
                    supabase.table("workoutlog").insert({
                        "owner_type": owner_type, "date": datetime.date.today().strftime("%Y-%m-%d"), 
                        "exercise": ex_name.title(), "muscle_group": muscle, "weight": w, "reps": r, "sets": s, 
                        "rpe": rpe, "rir": rir, "method": method, "assigned_day": days_vn.index(target_day), 
                        "one_rm": one_rm, "ex_type": ex_type
                    }).execute()
                    st.success("Đã phân bổ chiêu thức!")

    elif menu == "📈 Bản Đồ Chiến Lược":
        st.header("📊 Chiến Lược Gia")
        st.markdown(f"### ⚔️ MICROCYCLE (Tuần {current_week} / {meso_length})")
        st.progress(min(current_week / (meso_length + 1), 1.0))
        if current_week <= meso_length:
            if st.button("▶️ Chốt Tuần. Chuyển sang Tuần Tiếp Theo"):
                supabase.table("userprofile").update({"micro_week": current_week + 1}).eq("id", 1).execute()
                st.rerun()
        if current_week > meso_length:
            with st.form("deload"):
                next_goal = st.selectbox("Mục tiêu tới:", ["Hypertrophy", "Strength"])
                if st.form_submit_button("Hoàn thành Deload & Bắt đầu Chiến Dịch Mới"):
                    supabase.table("userprofile").update({"micro_week": 1, "meso_goal": next_goal}).eq("id", 1).execute()
                    st.rerun()

    elif menu == "⚙️ Tam Giác":
        st.header("⚙️ Cấu Hình Cốt Lõi")
        with st.form("triad_form"):
            c1, c2, c3 = st.columns(3)
            new_v = c1.selectbox("Khối lượng (Volume)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(v_lvl))
            new_i = c2.selectbox("Cường độ (Intensity)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(i_lvl))
            new_f = c3.selectbox("Tần suất (Frequency)", ["Thấp", "Vừa", "Cao"], index=["Thấp", "Vừa", "Cao"].index(f_lvl))
            if st.form_submit_button("Cập Nhật Gen Huấn Luyện"):
                supabase.table("userprofile").update({"vol_level": new_v, "int_level": new_i, "freq_level": new_f}).eq("id", 1).execute()
                st.rerun()

if __name__ == "__main__":
    main()