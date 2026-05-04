import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# ==========================================
# ĐIỀN URL VÀ KEY CỦA ĐẠO HỮU VÀO ĐÂY
# ==========================================
SUPABASE_URL_RAW = "https://kkdxkyoghdaneoblajng.supabase.co"
SUPABASE_KEY_RAW = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrZHhreW9naGRhbmVvYmxham5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc4NjkzODUsImV4cCI6MjA5MzQ0NTM4NX0.GmsHiN5F5KCnV5U0cjTa1adq2Mn371eORUCpPL44Ruw"

clean_url = SUPABASE_URL_RAW.strip().replace('/rest/v1', '').rstrip('/')
clean_key = SUPABASE_KEY_RAW.strip()

st.set_page_config(page_title="Eco Gym V21 - Volume Guard", page_icon="⚖️", layout="wide")

@st.cache_resource
def init_db() -> Client:
    return create_client(clean_url, clean_key)

try:
    supabase = init_db()
except Exception as e:
    st.error(f"🚨 LỖI KẾT NỐI: {e}")
    st.stop()

# THỨ TỰ ƯU TIÊN VÀ MỤC TIÊU VOLUME (10-20 sets/tuần)
MUSCLE_CONFIG = {
    "Ngực": {"order": 1, "min_vol": 10},
    "Lưng": {"order": 2, "min_vol": 10},
    "Đùi Trước": {"order": 3, "min_vol": 10},
    "Đùi Sau": {"order": 4, "min_vol": 8},
    "Vai": {"order": 5, "min_vol": 8},
    "Mông": {"order": 6, "min_vol": 6},
    "Tay Sau": {"order": 7, "min_vol": 6},
    "Tay Trước": {"order": 8, "min_vol": 6},
    "Bắp Chân": {"order": 9, "min_vol": 6},
    "Bụng": {"order": 10, "min_vol": 4}
}

def main():
    u_res = supabase.table("userprofile").select("*").eq("id", 1).execute()
    u = u_res.data[0]
    current_week = u["micro_week"]
    
    st.sidebar.title("🧬 ECO GYM V21")
    selected_name = st.sidebar.radio("👥 Người tập:", ["Tôi", u["buddy_name"]], horizontal=True)
    owner_type = "me" if selected_name == "Tôi" else "buddy"
    menu = st.sidebar.radio("Chuyển đến:", ["📅 Tác Chiến PPLxUL", "🏋️ Thêm Bài Tập", "📊 Kiểm Toán Volume"])

    # Lấy toàn bộ dữ liệu tuần này để tính toán Volume
    all_logs = supabase.table("workoutlog").select("*").eq("owner_type", owner_type).execute()
    df_logs = pd.DataFrame(all_logs.data) if all_logs.data else pd.DataFrame()

    if menu == "📅 Tác Chiến Hàng Ngày" or menu == "📅 Tác Chiến PPLxUL":
        st.header(f"📅 Lịch PPLxUL: {selected_name}")
        
        today_idx = datetime.datetime.today().weekday()
        cal_res = supabase.table("weeklycalendar").select("*").eq("owner_type", owner_type).order("day_index").execute()
        
        for day in cal_res.data:
            idx, name, focus = day["day_index"], day["day_name"], day["focus"]
            is_today = (idx == today_idx)
            
            with st.expander(f"{'📍' if is_today else '📅'} {name} - {focus}", expanded=is_today):
                day_logs = df_logs[df_logs['assigned_day'] == idx] if not df_logs.empty else pd.DataFrame()
                
                if not day_logs.empty:
                    # Lấy bài mới nhất từng loại
                    latest_day = day_logs.sort_values('id').groupby('exercise').last().reset_index()
                    
                    # Gom nhóm cơ
                    mgs = sorted(latest_day['muscle_group'].unique(), key=lambda x: MUSCLE_CONFIG.get(x, {"order": 99})["order"])
                    
                    for mg in mgs:
                        # KIỂM TOÁN VOLUME CHO NHÓM CƠ NÀY TRONG TUẦN
                        weekly_mg_vol = df_logs[df_logs['muscle_group'] == mg]['sets'].sum() if not df_logs.empty else 0
                        min_req = MUSCLE_CONFIG.get(mg, {"min_vol": 10})["min_vol"]
                        
                        col_h1, col_h2 = st.columns([3, 1])
                        col_h1.markdown(f"### 🛡️ {mg.upper()}")
                        
                        # Cảnh báo Volume
                        if weekly_mg_vol < min_req:
                            col_h2.warning(f"⚠️ Vol: {weekly_mg_vol}/{min_req} sets")
                        else:
                            col_h2.success(f"✅ Vol: {weekly_mg_vol} sets")

                        mg_exs = latest_day[latest_day['muscle_group'] == mg]
                        for _, ex in mg_exs.iterrows():
                            # Logic tự động tăng set nếu thiếu volume
                            suggest_sets = int(ex['sets'])
                            if weekly_mg_vol < min_req and is_today:
                                suggest_sets += 1
                                st.caption(f"💡 *Tự động tăng 1 set cho {ex['exercise']} để bù Volume tuần.*")

                            with st.expander(f"{ex['exercise']} ({ex['weight']}kg x {ex['reps']})"):
                                with st.form(key=f"f_{idx}_{ex['exercise']}"):
                                    c1, c2, c3 = st.columns(3)
                                    nw = c1.number_input("Tạ (kg)", value=float(ex['weight']), step=2.5)
                                    nr = c2.number_input("Reps", value=int(ex['reps']), step=1)
                                    ns = c3.number_input("Sets", value=suggest_sets, step=1)
                                    if st.form_submit_button("✅ Lưu"):
                                        supabase.table("workoutlog").insert({
                                            "owner_type": owner_type, "date": datetime.date.today().strftime("%Y-%m-%d"),
                                            "exercise": ex['exercise'], "muscle_group": mg, "weight": nw,
                                            "reps": nr, "sets": ns, "assigned_day": idx, "ex_type": ex.get('ex_type', 'Compound')
                                        }).execute()
                                        st.rerun()
                else:
                    st.info("Chưa có dữ liệu bài tập. Hãy thêm bài ở mục 'Thêm Bài Tập'.")

    elif menu == "📊 Kiểm Toán Volume":
        st.header("📊 Tổng Kết Volume Tuần")
        if not df_logs.empty:
            vol_summary = df_logs.groupby('muscle_group')['sets'].sum().reset_index()
            for _, row in vol_summary.iterrows():
                mg = row['muscle_group']
                vol = row['sets']
                min_v = MUSCLE_CONFIG.get(mg, {"min_vol": 10})["min_vol"]
                
                st.write(f"**{mg}**")
                progress = min(vol / (min_v * 1.5), 1.0)
                st.progress(progress)
                if vol < min_v:
                    st.error(f"🚨 Thiếu {min_v - vol} sets! Hãy thêm bài tập hoặc tăng set vào ngày {mg} tiếp theo.")
                elif vol > 20:
                    st.warning(f"⚡ Volume quá cao ({vol} sets). Coi chừng quá tải (Overtraining)!")
                else:
                    st.success(f"💎 Volume tối ưu: {vol} sets.")
        else:
            st.write("Chưa có dữ liệu tập luyện tuần này.")

    elif menu == "🏋️ Thêm Bài Tập":
        st.header("🏋️ Thiết Kế Giáo Án")
        with st.form("new_ex"):
            name = st.text_input("Tên bài tập")
            msc = st.selectbox("Nhóm cơ", list(MUSCLE_CONFIG.keys()))
            day = st.selectbox("Gán vào buổi:", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            typ = st.selectbox("Loại", ["Compound", "Isolation"])
            if st.form_submit_button("Lưu"):
                idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(day)
                supabase.table("workoutlog").insert({
                    "owner_type": owner_type, "exercise": name, "muscle_group": msc, 
                    "assigned_day": idx, "ex_type": typ, "weight": 0, "reps": 0, "sets": 2
                }).execute()
                st.success("Đã thêm!")

if __name__ == "__main__":
    main()