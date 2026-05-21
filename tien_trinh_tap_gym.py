import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
import json

# ==========================================
# CẤU HÌNH KẾT NỐI
# ==========================================
URL = "https://kkdxkyoghdaneoblajng.supabase.co/rest/v1/"
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

def get_method_note(method):
    notes = {
        "TOPSET": "Warm-up kỹ. 1 set nặng nhất (RPE 8-9). Back-off set giảm 15-20% tạ.",
        "Back-off Set": "Tạ giảm 15-20% so với Topset. RIR 1-2.",
        "Rest-Pause": "Đánh tới Failure. Nghỉ 15s -> Đánh tiếp tới Failure.",
        "Drop Set": "Đánh tới Failure. Tháo ngay 20-30% tạ đánh tiếp không nghỉ.",
        "Standard": "Straight sets. Nghỉ 2-3 phút."
    }
    return notes.get(method, "")

def main():
    st.set_page_config(page_title="Eco Gym V35 - Nutrition Master", layout="wide")
    
    user_req = supabase.table("userprofile").select("*").eq("id", 1).execute()
    if not user_req.data: st.stop()
    u = user_req.data[0]
    curr_w = u["micro_week"]
    
    st.sidebar.title("🧬 ECO GYM V35")
    menu = st.sidebar.selectbox("CHỌN MỤC TIÊU:", [
        "1. 📅 LỊCH TẬP (VETERAN)", 
        "2. 🏋️ THÊM BÀI TẬP", 
        "3. 🧘 PHÂN KỲ & DELOAD", 
        "4. 📈 TRACKING & DỌN DẸP", 
        "5. 👤 BODY & CALO"
    ])

    # ---------------------------------------------------------
    # MỤC 1: LỊCH TẬP
    # ---------------------------------------------------------
    if menu == "1. 📅 LỊCH TẬP (VETERAN)":
        st.header(f"📅 Tác Chiến (Tuần {curr_w})")
        today_idx = datetime.datetime.today().weekday()
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        cal = supabase.table("weeklycalendar").select("*").eq("owner_type", "me").order("day_index").execute().data
        
        for day in cal:
            idx, name, focus = day["day_index"], day["day_name"], day["focus"]
            with st.expander(f"{'📍' if idx == today_idx else '📅'} {name}: {focus}", expanded=(idx==today_idx)):
                
                c_d1, c_d2 = st.columns([2, 1])
                new_day = c_d1.selectbox("Dời lịch sang:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], key=f"move_{idx}", label_visibility="collapsed")
                if c_d2.button(f"🔄 Dời toàn bộ", key=f"btn_move_{idx}"):
                    new_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(new_day)
                    supabase.table("workoutlog").update({"assigned_day": new_idx}).eq("assigned_day", idx).execute()
                    st.rerun()

                if idx in [3, 5]:
                    st.markdown("---")
                    st.caption("🧬 **Flex Mode:** Tự do điều chỉnh mục tiêu buổi tập Thân Dưới để bơm bù Volume.")
                    cf1, cf2 = st.columns([3, 1])
                    flex_opt = cf1.selectbox("Chuyển đổi mục tiêu buổi tập:", 
                        ["Đùi / Mông / Bắp Chân", "Chân (Lower)", "Tập Ngực (Bù Volume)", "Tập Lưng (Bù Volume)", "Tập Vai / Tay", "Linh Hoạt (Tự Chọn)"],
                        key=f"flex_opt_{idx}", label_visibility="collapsed")
                    if cf2.button("Chuyển Form", key=f"btn_flex_{idx}"):
                        supabase.table("weeklycalendar").update({"focus": flex_opt}).eq("day_index", idx).execute()
                        st.success("Đã thay đổi chiến thuật buổi tập!")
                        st.rerun()

                st.markdown("---")
                exs = supabase.table("workoutlog").select("*").eq("assigned_day", idx).execute().data
                if exs:
                    templates = [x for x in exs if x['date'] == '2000-01-01']
                    if not templates:
                        df_mig = pd.DataFrame(exs).sort_values(by=['id']).drop_duplicates('exercise', keep='last')
                        for _, r in df_mig.iterrows():
                            supabase.table("workoutlog").update({"date": "2000-01-01", "micro_week": 0}).eq("id", r['id']).execute()
                        st.rerun()

                    df = pd.DataFrame(templates).sort_values(by=['id']).drop_duplicates('exercise', keep='last')
                    is_ul = "upper" in focus.lower() or "lower" in focus.lower() or "chân" in focus.lower()
                    
                    df['sort_tuple'] = df.apply(lambda r: (
                        MUSCLE_CONFIG.get(r['muscle_group'], {}).get('order', 99) if not is_ul else 0,
                        0 if "Compound" in str(r['ex_type']) else 1,
                        r['id']
                    ), axis=1)
                    df = df.sort_values(by=['sort_tuple'])
                    
                    today_logs = [x for x in exs if x['date'] == today_str and x['micro_week'] == curr_w]
                    if today_logs and idx == today_idx:
                        st.success("✅ Bạn đã CHỐT SỔ buổi tập này!")

                    for _, row in df.iterrows():
                        icon = "🔴" if "Compound" in str(row['ex_type']) else "🔵"
                        title = f"{icon} {row['exercise']} | {row['sets']} Sets x {row['weight']}kg"
                        
                        with st.expander(title):
                            with st.form(key=f"f_{idx}_{row['id']}"):
                                c_info1, c_info2 = st.columns([1, 1])
                                c_info1.caption(f"**Cơ:** {row['muscle_group']} | **Loại:** {row['ex_type']}")
                                c_info2.caption(f"**Method:** {row['method']}")
                                
                                with st.expander("💡 Gợi ý phương pháp"):
                                    st.write(get_method_note(row['method']))
                                
                                c1, c2, c3 = st.columns(3)
                                nw = c1.number_input("Tạ (kg)", value=float(row['weight']), step=2.5)
                                nr = c2.number_input("Reps", value=int(row['reps']), step=1)
                                ns = c3.number_input("Working Sets", value=int(row['sets']), step=1)
                                
                                c4, c5 = st.columns(2)
                                nrpe = c4.number_input("RPE", value=float(row['rpe']), step=0.5)
                                note = c5.text_input("Ghi chú", value=str(row.get('notes', '') or ''))
                                
                                c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 1])
                                if c_btn1.form_submit_button("✏️ Cập Nhật Tạ (Lưu Nháp)"):
                                    supabase.table("workoutlog").update({
                                        "weight": nw, "reps": nr, "sets": ns, "rpe": nrpe, "notes": note
                                    }).eq("id", row['id']).execute()
                                    st.rerun()
                                    
                                if c_btn2.form_submit_button("📦 Lưu Kho"):
                                    supabase.table("workoutlog").update({"assigned_day": 99}).eq("id", row['id']).execute()
                                    st.rerun()
                                    
                                if c_btn3.form_submit_button("❌ Xóa Hẳn"):
                                    supabase.table("workoutlog").delete().eq("id", row['id']).execute()
                                    st.rerun()
                    
                    st.markdown("---")
                    if st.button(f"🏁 XÁC NHẬN HOÀN THÀNH BUỔI TẬP", key=f"finish_day_{idx}", use_container_width=True):
                        if today_logs:
                            ids_to_delete = [x['id'] for x in today_logs]
                            for chunk in [ids_to_delete[i:i + 100] for i in range(0, len(ids_to_delete), 100)]:
                                supabase.table("workoutlog").delete().in_("id", chunk).execute()
                        
                        new_inserts = []
                        for _, r in df.iterrows():
                            if int(r['sets']) > 0:
                                new_inserts.append({
                                    "owner_type": "me", "date": today_str,
                                    "exercise": r['exercise'], "muscle_group": r['muscle_group'], 
                                    "weight": float(r['weight']), "reps": int(r['reps']), "sets": int(r['sets']), 
                                    "rpe": float(r['rpe']), "rir": int(r['rir']), "method": r['method'],
                                    "assigned_day": idx, "ex_type": r['ex_type'], "micro_week": curr_w,
                                    "notes": str(r.get('notes', '') or '')
                                })
                        if new_inserts:
                            supabase.table("workoutlog").insert(new_inserts).execute()
                            st.success("🎉 Đã CHỐT SỔ thành công!")
                            st.rerun()
                else:
                    st.info("Chưa có bài tập.")

    # ---------------------------------------------------------
    # MỤC 2: THÊM BÀI TẬP
    # ---------------------------------------------------------
    elif menu == "2. 🏋️ THÊM BÀI TẬP":
        st.header("🏋️ Thiết Kế Chiêu Thức Mới")
        preview_method = st.selectbox("Chọn Phương pháp tập:", ["Standard", "TOPSET", "Back-off Set", "Rest-Pause", "Drop Set"])
        st.info(get_method_note(preview_method))

        with st.form("add_ex"):
            name = st.text_input("Tên bài tập:")
            mg = st.selectbox("Nhóm cơ chính:", list(MUSCLE_CONFIG.keys()))
            
            c1, c2, c3 = st.columns(3)
            rpe = c1.slider("RPE Target", 5.0, 10.0, 8.0, step=0.5)
            rir = c2.number_input("RIR Target", 0, 5, 1)
            typ = c3.selectbox("Loại bài", ["Compound", "Isolation"])
            day = st.selectbox("Gán vào thứ:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            
            if st.form_submit_button("Lưu Bài Tập"):
                if not name.strip(): st.error("⚠️ Điền tên bài!")
                else:
                    d_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(day)
                    supabase.table("workoutlog").insert({
                        "exercise": name.strip().title(), "muscle_group": mg, "method": preview_method, 
                        "rpe": rpe, "rir": rir, "ex_type": typ, "assigned_day": d_idx, 
                        "owner_type": "me", "sets": 2, "weight": 0, "reps": 0, "micro_week": 0, "date": "2000-01-01"
                    }).execute()
                    st.success("Đã nạp vào giáo án!")

    # ---------------------------------------------------------
    # MỤC 3: PHÂN KỲ & DELOAD
    # ---------------------------------------------------------
    elif menu == "3. 🧘 PHÂN KỲ & DELOAD":
        st.header("🧘 Phân Kỳ Tập Luyện")
        st.subheader("🌍 MACROCYCLE (Mục tiêu Dài hạn)")
        m_type = u.get("macro_type") or "Tăng cơ (Hypertrophy)"
        try: pr_dict = json.loads(u.get("pr_targets") or "{}")
        except: pr_dict = {}

        all_logs = supabase.table("workoutlog").select("exercise, ex_type").execute().data
        compound_exs = sorted(list(set([e['exercise'] for e in all_logs if "Compound" in str(e.get('ex_type', ''))])))
        selected_prs = st.multiselect("Theo dõi PR cho các bài Compound:", compound_exs, default=[c for c in pr_dict.keys() if c in compound_exs])

        with st.form("macro_form"):
            new_m_type = st.radio("Định hướng chu kỳ:", ["Tăng cơ (Hypertrophy)", "Tăng sức mạnh (Strength)"], index=0 if "cơ" in m_type else 1)
            pr_inputs = {}
            if selected_prs:
                cols = st.columns(3)
                for i, ex in enumerate(selected_prs):
                    with cols[i % 3]:
                        pr_inputs[ex] = st.number_input(f"{ex} (kg)", value=float(pr_dict.get(ex, 0.0)), step=2.5)
            
            if st.form_submit_button("Cập Nhật Kỷ Lục"):
                supabase.table("userprofile").update({"macro_type": new_m_type, "pr_targets": json.dumps(pr_inputs)}).eq("id", 1).execute()
                st.success("Đã ghi nhận!")
                st.rerun()

        st.markdown("---")
        st.subheader("🛡️ MICROCYCLE (Deload)")
        m_len = u["meso_length"]
        
        if curr_w > m_len:
            st.error(f"⚠️ TRẠNG THÁI: DELOAD (Tuần {curr_w})")
            if st.button("🏁 Khởi động Chu kỳ mới (Reset Volume & Tuần về 1)"):
                supabase.table("userprofile").update({"micro_week": 1}).eq("id", 1).execute()
                st.rerun()
        else:
            st.success(f"🔥 Tuần tập: {curr_w} / {m_len}")
            if st.button("➡️ Hoàn thành Tuần -> Qua tuần tiếp theo"):
                supabase.table("userprofile").update({"micro_week": curr_w + 1}).eq("id", 1).execute()
                st.rerun()

    # ---------------------------------------------------------
    # MỤC 4: TRACKING & DỌN DẸP
    # ---------------------------------------------------------
    elif menu == "4. 📈 TRACKING & DỌN DẸP":
        st.header("📈 Tracking & Chống Nặng Máy")
        logs_data = supabase.table("workoutlog").select("*").execute().data
        logs = pd.DataFrame(logs_data)
        
        if not logs.empty:
            logs['micro_week'] = pd.to_numeric(logs.get('micro_week', 1)).fillna(1).astype(int)
            
            st.subheader(f"📊 Volume Tuần Này (Tuần {curr_w})")
            cw_logs = logs[(logs['micro_week'] == curr_w) & (logs['date'] != '2000-01-01')]
            
            if cw_logs.empty:
                st.info("Tuần này chưa có dữ liệu Chốt Sổ.")
            else:
                vol = cw_logs.groupby('muscle_group')['sets'].sum().reset_index()
                for _, row in vol.iterrows():
                    mg, s = row['muscle_group'], row['sets']
                    if s < 10: st.warning(f"**{mg}**: {s} sets (Thiếu)")
                    elif s > 20: st.error(f"**{mg}**: {s} sets (Quá tải)")
                    else: st.success(f"**{mg}**: {s} sets (Tối ưu)")
            
            st.markdown("---")
            st.subheader("🏋️ Tracking Tăng Tiến Lịch Sử")
            history_df = logs[logs['date'] != '2000-01-01'].copy()
            
            if not history_df.empty:
                history_df['1RM_Est'] = (history_df['weight'] * (1 + history_df['reps'] / 30)).round(1)
                history_df = history_df.sort_values(by=['date', 'id'], ascending=[False, False])
                mgs_sorted = sorted(history_df['muscle_group'].unique(), key=lambda x: MUSCLE_CONFIG.get(x, {}).get('order', 99))
                
                tabs = st.tabs([mg.upper() for mg in mgs_sorted])
                for i, mg in enumerate(mgs_sorted):
                    with tabs[i]:
                        mg_data = history_df[history_df['muscle_group'] == mg]
                        display_cols = ['date', 'micro_week', 'ex_type', 'exercise', 'weight', 'reps', '1RM_Est', 'sets', 'rpe', 'notes']
                        display_cols = [c for c in display_cols if c in mg_data.columns]
                        st.dataframe(mg_data[display_cols], use_container_width=True)
                        
                        st.markdown("---")
                        del_options = {f"[W{r['micro_week']} - {r['date']}] {r['exercise']} - {r['weight']}kg": r for _, r in mg_data.iterrows()}
                        if del_options:
                            c_del1, c_del2 = st.columns([3, 1])
                            del_choice = c_del1.selectbox("Sửa Sai: Chọn Log để Xóa", list(del_options.keys()), key=f"del_{mg}")
                            
                            if c_del2.button("❌ Xóa Lịch Sử Này", key=f"btn_del_{mg}"):
                                target_log = del_options[del_choice]
                                supabase.table("workoutlog").delete().eq("id", target_log['id']).execute()
                                st.rerun()

            st.markdown("---")
            st.subheader("🧹 LÒ BÁT QUÁI - DỌN DẸP")
            clean_option = st.selectbox("Mức độ dọn dẹp:", [
                "1. Xóa dữ liệu cũ hơn 1 THÁNG",
                "2. Xóa dữ liệu cũ hơn 3 THÁNG",
                "3. 🔥 Xóa TOÀN BỘ lịch sử (Giữ nguyên khung Lịch tập)"
            ])
            
            if st.button("🚨 Thực Thi Dọn Dẹp"):
                if "1 THÁNG" in clean_option: cutoff = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
                elif "3 THÁNG" in clean_option: cutoff = (datetime.date.today() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
                else: cutoff = "9999-12-31"
                
                ids_to_del = [r['id'] for r in logs_data if r['date'] < cutoff and r['date'] != "2000-01-01"]
                if ids_to_del:
                    for chunk in [ids_to_del[i:i + 100] for i in range(0, len(ids_to_del), 100)]:
                        supabase.table("workoutlog").delete().in_("id", chunk).execute()
                    st.success(f"Đã thanh tẩy {len(ids_to_del)} dòng dữ liệu cũ!")
                else:
                    st.info("Không có rác cũ để xóa.")
                st.rerun()

    # ---------------------------------------------------------
    # MỤC 5: BODY & CALO (KIỂM SOÁT THỦ CÔNG CHI TIẾT)
    # ---------------------------------------------------------
    elif menu == "5. 👤 BODY & CALO":
        st.header("👤 Body & Dinh Dưỡng Thủ Công")
        
        with st.form("body_info_manual"):
            st.subheader("1. Chỉ Số Cơ Thể")
            c1, c2, c3 = st.columns(3)
            h = c1.number_input("Chiều cao (cm)", value=float(u.get('height', 178.0)))
            w = c2.number_input("Cân nặng (kg)", value=float(u.get('weight', 90.0)))
            bf = c3.number_input("Body Fat (%)", value=float(u.get('body_fat', 24.0) or 24.0))
            
            st.markdown("---")
            st.subheader("2. Thiết Lập Calo (Manual)")
            goal = st.selectbox("Giai đoạn hiện tại (Phase):", ["Cutting", "Mini-cutting", "Bulking", "Recomposition"], index=0)
            
            c_cal1, c_cal2, c_cal3 = st.columns(3)
            maint_cal = c_cal1.number_input("Calo Duy Trì (Maintenance)", value=int(u.get('maintenance_cal', 2500) or 2500), step=50)
            def_cal = c_cal2.number_input("Calo Thâm Thụt (Cutting/Mini)", value=int(u.get('deficit_cal', 2000) or 2000), step=50)
            sur_cal = c_cal3.number_input("Calo Thặng Dư (Bulking)", value=int(u.get('surplus_cal', 2800) or 2800), step=50)

            st.markdown("---")
            st.subheader("3. Phân Bổ Macros (Mục Tiêu Mỗi Ngày)")
            st.caption("Hãy nhập số Gam bạn mong muốn. Hệ thống sẽ tự quy đổi ra Calo để bạn đối chiếu.")
            
            c_m1, c_m2, c_m3 = st.columns(3)
            pro = c_m1.number_input("🥩 Đạm (Protein) - Gam", value=int(u.get('protein_target', 160) or 160), step=5)
            carb = c_m2.number_input("🍚 Tinh bột (Carb) - Gam", value=int(u.get('carb_target', 200) or 200), step=5)
            fat = c_m3.number_input("🥑 Chất béo (Fat) - Gam", value=int(u.get('fat_target', 60) or 60), step=5)
            
            # Tính toán Calo hiển thị ngay lập tức (Không lưu, chỉ để xem)
            pro_cal = pro * 4
            carb_cal = carb * 4
            fat_cal = fat * 9
            total_macro_cal = pro_cal + carb_cal + fat_cal
            
            c_m1.info(f"👉 {pro}g x 4 = **{pro_cal} kcal**")
            c_m2.info(f"👉 {carb}g x 4 = **{carb_cal} kcal**")
            c_m3.info(f"👉 {fat}g x 9 = **{fat_cal} kcal**")
            
            st.markdown(f"⚡ **Tổng Calo từ Macros:** `{total_macro_cal} kcal` (Hãy tự đối chiếu số này với mức Calo mục tiêu ở trên).")

            if st.form_submit_button("💾 Ghi Nhận Toàn Bộ Thông Số"):
                supabase.table("userprofile").update({
                    "height": h, "weight": w, "body_fat": bf, "goal_type": goal,
                    "maintenance_cal": maint_cal, "deficit_cal": def_cal, "surplus_cal": sur_cal,
                    "protein_target": pro, "carb_target": carb, "fat_target": fat
                }).eq("id", 1).execute()
                st.success("Đã ghi nhận toàn bộ thông số dinh dưỡng!")

if __name__ == "__main__":
    main()
