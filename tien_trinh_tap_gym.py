import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import json

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
    "Ngực": {"order": 1}, "Lưng": {"order": 2}, "Đùi Trước": {"order": 3},
    "Vai": {"order": 4}, "Tay Sau": {"order": 5}, "Tay Trước": {"order": 6},
    "Đùi Sau": {"order": 7}, "Mông": {"order": 8}, "Bắp Chân": {"order": 9}, "Bụng": {"order": 10}
}

def main():
    st.set_page_config(page_title="Eco Gym V27 - Master System", layout="wide")
    
    user_req = supabase.table("userprofile").select("*").eq("id", 1).execute()
    if not user_req.data: st.stop()
    u = user_req.data[0]
    
    st.sidebar.title("🧬 ECO GYM V27")
    menu = st.sidebar.selectbox("CHỌN MỤC TIÊU:", [
        "1. 📅 LỊCH TẬP LINH HOẠT", 
        "2. 🏋️ THÊM BÀI TẬP (THỦ CÔNG)", 
        "3. 🧘 CƠ CHẾ DELOAD", 
        "4. 📈 THỐNG KÊ & TĂNG TIẾN", 
        "5. 👤 CHỈ SỐ CƠ THỂ & CALO"
    ])

    # ---------------------------------------------------------
    # MỤC 1: LỊCH TẬP LINH HOẠT & HIỂN THỊ THÔNG MINH
    # ---------------------------------------------------------
    if menu == "1. 📅 LỊCH TẬP LINH HOẠT":
        st.header("📅 Khung Lịch Tập Di Động")
        today_idx = datetime.datetime.today().weekday()
        cal = supabase.table("weeklycalendar").select("*").eq("owner_type", "me").order("day_index").execute().data
        
        for day in cal:
            idx, name, focus = day["day_index"], day["day_name"], day["focus"]
            with st.expander(f"{'📍' if idx == today_idx else '📅'} {name}: {focus}", expanded=(idx==today_idx)):
                # Tính năng Dời Lịch
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
                    # Lấy bài mới nhất của từng tên bài
                    df = pd.DataFrame(exs).sort_values(by=['id']).drop_duplicates('exercise', keep='last')
                    
                    # LOGIC SẮP XẾP RẠCH RÒI PPL vs UPPER/LOWER
                    is_ul = "upper" in focus.lower() or "lower" in focus.lower()
                    
                    def custom_sort(row):
                        m_order = MUSCLE_CONFIG.get(row['muscle_group'], {}).get('order', 99) if not is_ul else 0
                        t_order = 0 if "Compound" in str(row['ex_type']) else 1
                        return (m_order, t_order, row['id'])
                    
                    df['sort_tuple'] = df.apply(custom_sort, axis=1)
                    df = df.sort_values(by=['sort_tuple'])
                    
                    for _, row in df.iterrows():
                        icon = "🔴" if "Compound" in str(row['ex_type']) else "🔵"
                        title = f"{icon} {row['exercise']} | {row['sets']}x{row['weight']}kg - {row['reps']}reps - {row['rpe']}RPE"
                        
                        with st.expander(title):
                            with st.form(key=f"f_{idx}_{row['id']}"):
                                st.caption(f"Nhóm cơ: {row['muscle_group']} | Loại: {row['ex_type']} | Phương pháp: {row['method']}")
                                c1, c2, c3, c4 = st.columns(4)
                                nw = c1.number_input("Tạ (kg)", value=float(row['weight']), step=2.5)
                                nr = c2.number_input("Reps", value=int(row['reps']), step=1)
                                ns = c3.number_input("Sets", value=int(row['sets']), step=1)
                                
                                c_btn1, c_btn2 = st.columns([2, 1])
                                if c_btn1.form_submit_button("✅ Cập nhật Set"):
                                    supabase.table("workoutlog").insert({
                                        "owner_type": "me", "date": datetime.date.today().strftime("%Y-%m-%d"),
                                        "exercise": row['exercise'], "muscle_group": row['muscle_group'], 
                                        "weight": nw, "reps": nr, "sets": ns, 
                                        "rpe": row['rpe'], "rir": row['rir'], "method": row['method'],
                                        "assigned_day": idx, "ex_type": row['ex_type']
                                    }).execute()
                                    st.rerun()
                                if c_btn2.form_submit_button("🗑️ Xóa Bài Này"):
                                    supabase.table("workoutlog").delete().eq("exercise", row['exercise']).eq("assigned_day", idx).execute()
                                    st.rerun()
                else:
                    st.info("Chưa có bài tập nào.")

    # ---------------------------------------------------------
    # MỤC 2: THÊM BÀI TẬP (THỦ CÔNG)
    # ---------------------------------------------------------
    elif menu == "2. 🏋️ THÊM BÀI TẬP (THỦ CÔNG)":
        st.header("🏋️ Thiết Kế Chiêu Thức")
        with st.form("add_ex"):
            name = st.text_input("Tên bài tập:")
            mg = st.selectbox("Nhóm cơ tác động chính:", list(MUSCLE_CONFIG.keys()))
            method = st.selectbox("Phương pháp:", ["Standard", "TOPSET", "Back-off Set", "Rest-Pause", "Drop Set"])
            c1, c2, c3 = st.columns(3)
            rpe = c1.slider("RPE Target", 5.0, 10.0, 8.0, step=0.5)
            rir = c2.number_input("RIR Target", 0, 5, 1)
            typ = c3.selectbox("Loại", ["Compound", "Isolation"])
            day = st.selectbox("Gán vào thứ:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            
            if st.form_submit_button("Lưu Bài Tập"):
                if not name.strip():
                    st.error("⚠️ Phải nhập tên bài tập!")
                else:
                    d_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(day)
                    supabase.table("workoutlog").insert({
                        "exercise": name.strip().title(), "muscle_group": mg, "method": method, "rpe": rpe, "rir": rir,
                        "ex_type": typ, "assigned_day": d_idx, "owner_type": "me", "sets": 2, "weight": 0, "reps": 0
                    }).execute()
                    st.success("Đã thêm vào giáo án!")

    # ---------------------------------------------------------
    # MỤC 3: CƠ CHẾ DELOAD VÀ MACROCYCLE
    # ---------------------------------------------------------
    elif menu == "3. 🧘 CƠ CHẾ DELOAD":
        st.header("🧘 Phân Kỳ & Giao Thức Phục Hồi")
        
        # MACROCYCLE (Dài hạn)
        st.subheader("🌍 MACROCYCLE (Mục tiêu Dài hạn)")
        m_type = u.get("macro_type") or "Tăng cơ (Hypertrophy)"
        pr_targets = u.get("pr_targets") or "{}"
        try: pr_dict = json.loads(pr_targets)
        except: pr_dict = {}

        # Quét lấy tất cả bài tập Compound hiện có trong dữ liệu
        all_logs = supabase.table("workoutlog").select("exercise, ex_type").execute().data
        compound_exs = sorted(list(set([e['exercise'] for e in all_logs if "Compound" in str(e.get('ex_type', ''))])))
        
        st.write("🎯 **Lựa chọn bài tập để phá kỷ lục PR:**")
        if not compound_exs:
            st.info("💡 Bạn chưa có bài tập Compound nào. Hãy vào Mục 2 để thêm bài tập nhé!")
            selected_prs = []
        else:
            # Tự động load các bài đã chọn trước đó
            default_selections = [c for c in pr_dict.keys() if c in compound_exs]
            selected_prs = st.multiselect("Chọn bài tập (Tự động lấy từ lịch tập của bạn):", compound_exs, default=default_selections)

        with st.form("macro_form"):
            new_m_type = st.radio("Định hướng chu kỳ lớn:", ["Tăng cơ (Hypertrophy)", "Tăng sức mạnh (Strength)"], index=0 if "cơ" in m_type else 1)
            
            pr_inputs = {}
            if selected_prs:
                st.write("**Nhập mức tạ mục tiêu (kg):**")
                cols = st.columns(3)
                for i, ex in enumerate(selected_prs):
                    with cols[i % 3]:
                        pr_inputs[ex] = st.number_input(f"{ex}", value=float(pr_dict.get(ex, 0.0)), step=2.5)
            
            if st.form_submit_button("Lưu Mục Tiêu Macrocycle"):
                new_pr = json.dumps(pr_inputs)
                supabase.table("userprofile").update({"macro_type": new_m_type, "pr_targets": new_pr}).eq("id", 1).execute()
                st.success("Đã cập nhật chiến lược và kỷ lục PR mới!")
                st.rerun()

        st.markdown("---")
        # MICROCYCLE (Ngắn hạn / Deload)
        st.subheader("🛡️ MICROCYCLE (Deload Ngắn Hạn)")
        curr_w, m_len = u["micro_week"], u["meso_length"]
        
        if curr_w > m_len:
            st.error(f"⚠️ TRẠNG THÁI: TUẦN DELOAD (Tuần {curr_w})")
            st.info("Mức tạ tuần này sẽ dao động 30-50% so với trước đó. Volume sẽ tự động cắt giảm 50%.")
            
            if st.button("🏁 Hoàn thành Deload -> Giảm Volume & Khởi động Meso Mới"):
                # Cắt giảm 40-50% volume cho chu kỳ mới và đưa về tuần 1
                exs = supabase.table("workoutlog").select("*").execute().data
                if exs:
                    df = pd.DataFrame(exs).sort_values(by=['id']).drop_duplicates('exercise', keep='last')
                    for _, row in df.iterrows():
                        new_sets = max(1, int(row['sets'] * 0.5)) # Giảm 50% số sets
                        supabase.table("workoutlog").insert({
                            "owner_type": "me", "date": datetime.date.today().strftime("%Y-%m-%d"),
                            "exercise": row['exercise'], "muscle_group": row['muscle_group'], 
                            "weight": row['weight'], "reps": row['reps'], "sets": new_sets, 
                            "rpe": row['rpe'], "rir": row['rir'], "method": row['method'],
                            "assigned_day": row['assigned_day'], "ex_type": row['ex_type']
                        }).execute()
                supabase.table("userprofile").update({"micro_week": 1}).eq("id", 1).execute()
                st.success("Đã đưa Volume về mức khởi tạo cho chu kỳ mới!")
                st.rerun()
        else:
            st.success(f"🔥 Tiến độ chu kỳ: Tuần {curr_w} / {m_len}")
            if st.button("➡️ Chốt tuần & Bước sang tuần tiếp theo"):
                supabase.table("userprofile").update({"micro_week": curr_w + 1}).eq("id", 1).execute()
                st.rerun()

    # ---------------------------------------------------------
    # MỤC 4: THỐNG KÊ VOLUME & QUẢN LÝ LỖI
    # ---------------------------------------------------------
    elif menu == "4. 📈 THỐNG KÊ & TĂNG TIẾN":
        st.header("📈 Kiểm Toán Volume & Lịch Sử Tăng Tiến")
        logs = pd.DataFrame(supabase.table("workoutlog").select("*").execute().data)
        
        if not logs.empty:
            st.subheader("📊 Tổng Số Sets Tuần Này")
            st.caption("Mức tối ưu để tăng cơ là 10-20 sets/tuần cho từng nhóm.")
            vol = logs.groupby('muscle_group')['sets'].sum().reset_index()
            for _, row in vol.iterrows():
                mg, s = row['muscle_group'], row['sets']
                if s < 10: st.warning(f"**{mg}**: {s} sets (Thiếu Volume)")
                elif s > 20: st.error(f"**{mg}**: {s} sets (Cảnh báo Quá tải)")
                else: st.success(f"**{mg}**: {s} sets (Tối ưu)")
            
            st.markdown("---")
            st.subheader("🏋️ Quá Trình Tăng Tiến Mức Tạ")
            st.caption("Bảng dữ liệu toàn bộ lịch sử tập luyện phân chia theo nhóm cơ để dễ dàng theo dõi.")
            
            # Sắp xếp để lấy toàn bộ lịch sử
            history_df = logs.sort_values(by=['date', 'id'], ascending=[False, False])
            mgs_present = history_df['muscle_group'].unique()
            mgs_sorted = sorted(mgs_present, key=lambda x: MUSCLE_CONFIG.get(x, {}).get('order', 99))
            
            # Tạo các TABS cho từng nhóm cơ
            tabs = st.tabs([mg.upper() for mg in mgs_sorted])
            for i, mg in enumerate(mgs_sorted):
                with tabs[i]:
                    mg_data = history_df[history_df['muscle_group'] == mg]
                    # Hiển thị bảng dạng DataFrame gọn gàng
                    st.dataframe(mg_data[['date', 'ex_type', 'exercise', 'weight', 'reps', 'sets', 'rpe']], use_container_width=True)

            st.markdown("---")
            st.subheader("🗑️ Khắc Phục Sai Sót (Xóa Log)")
            st.caption("Nếu lỡ bấm nhầm thêm bài hoặc qua tuần sai, chọn dòng để xóa:")
            
            logs_for_delete = logs.sort_values(by=['id'], ascending=False).head(30)
            del_options = {f"[{r['date']}] {r['exercise']} - {r['weight']}kg": r['id'] for _, r in logs_for_delete.iterrows()}
            del_choice = st.selectbox("Chọn Log muốn xóa bỏ:", list(del_options.keys()))
            
            if st.button("❌ Xóa Vĩnh Viễn Log Này"):
                log_id = del_options[del_choice]
                supabase.table("workoutlog").delete().eq("id", log_id).execute()
                st.success("Đã thanh tẩy dòng dữ liệu lỗi!")
                st.rerun()
        else:
            st.info("Chưa có dữ liệu thống kê.")

    # ---------------------------------------------------------
    # MỤC 5: CHỈ SỐ CƠ THỂ & CALO (NHẬP THỦ CÔNG)
    # ---------------------------------------------------------
    elif menu == "5. 👤 CHỈ SỐ CƠ THỂ & CALO":
        st.header("👤 Hồ Sơ Cá Nhân & Dinh Dưỡng")
        with st.expander("📚 BẢNG CÔNG THỨC THAM KHẢO (Bấm để xem)"):
            st.markdown("""
            **1. TDEE Thực Chiến:** `Cân nặng (kg) x Hệ số (30 - 45)`
            **2. Thâm thụt Calo:** Cutting: TDEE - (300 đến 500) | Bulking: TDEE + (200 đến 300)
            """)

        with st.form("body_info_manual"):
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Chiều cao (cm)", value=float(u.get('height', 178.0)))
            w = c2.number_input("Cân nặng (kg)", value=float(u.get('weight', 90.0)))
            bf = c3.number_input("Tỷ lệ mỡ - Body Fat (%)", value=float(u.get('body_fat', 24.0) or 24.0))
            
            st.markdown("---")
            c4, c5 = st.columns(2)
            goal = c4.selectbox("Phương pháp:", ["Cutting", "Mini-cutting", "Bulking", "Recomposition"], index=0)
            manual_tdee = c5.number_input("TDEE Tự Tính (kcal)", value=int(u.get('tdee_method', 2500) or 2500), step=50)
            target_cal = st.number_input("Mục tiêu Calo hằng ngày (kcal)", value=int(u.get('daily_calories', 2200) or 2200), step=50)

            if st.form_submit_button("💾 Lưu Trữ Dữ Liệu"):
                supabase.table("userprofile").update({
                    "height": h, "weight": w, "body_fat": bf,
                    "goal_type": goal, "tdee_method": str(manual_tdee), "daily_calories": target_cal
                }).eq("id", 1).execute()
                st.success("Đã ghi nhận!")

if __name__ == "__main__":
    main()