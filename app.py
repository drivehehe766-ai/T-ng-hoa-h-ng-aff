import streamlit as st
import pandas as pd
import re
from datetime import date

# Cấu hình trang
st.set_page_config(page_title="Tổng hợp đơn TikTok Affiliate", layout="wide")

st.title("📊 Dashboard Tổng Hợp Đơn Hàng TikTok Affiliate")
st.markdown("Hệ thống tự động trích xuất Tên sản phẩm, GMV, % Hoa hồng, Tiền nhận được cuối cùng, Trạng thái và Lọc theo ngày.")

uploaded_file = st.file_uploader("Tải lên file Excel xuất từ TikTok của bạn", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Đọc file dữ liệu
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("Đọc file thành công!")
        
        # Cố định tên các cột theo đúng yêu cầu
        col_product = "Tên sản phẩm"
        col_gmv = "GMV"
        col_percent = "Tiêu chuẩn"
        col_commission = "Tổng số tiền nhận được cuối cùng"
        col_status = "Trạng thái quyết toán đơn hàng"
        col_date = "Ngày đặt hàng"
        
        # Kiểm tra xem file có đủ 6 cột này không
        required_cols = [col_product, col_gmv, col_percent, col_commission, col_status, col_date]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"File tải lên bị thiếu các cột: {', '.join(missing_cols)}. Vui lòng kiểm tra lại file.")
        else:
            # --- HÀM XỬ LÝ TIỀN TỆ ---
            def get_correct_money(val):
                if pd.isna(val): return 0
                val_str = str(val).strip()
                try:
                    num = float(val_str.replace(',', ''))
                    # Nhân 1000 cho các số bị TikTok rút gọn (như 47.96 thành 47960)
                    if num > 0 and num < 1000:
                        num = num * 1000
                    return num
                except:
                    digits_only = re.sub(r'[^\d]', '', val_str)
                    return float(digits_only) if digits_only else 0

            # --- TRÍCH XUẤT VÀ XỬ LÝ DỮ LIỆU ---
            summary_table = df[required_cols].copy()
            # Xử lý định dạng tiền và đổi tên cột hiển thị
            summary_table["GMV đơn hàng"] = summary_table[col_gmv].apply(get_correct_money)
            summary_table["% Hoa hồng"] = summary_table[col_percent]
            summary_table["Tiền thực nhận (VNĐ)"] = summary_table[col_commission].apply(get_correct_money)
            
            # Xử lý cột Ngày tháng (Chuyển chuỗi văn bản thành định dạng Ngày)
            summary_table['Ngày chuẩn'] = pd.to_datetime(summary_table[col_date], format='%d/%m/%Y %H:%M:%S', errors='coerce').dt.date
            
            st.divider()
            
            # --- TÌM NGÀY NHỎ NHẤT VÀ LỚN NHẤT TRONG FILE ---
            valid_dates = summary_table['Ngày chuẩn'].dropna()
            
            if not valid_dates.empty:
                min_date_val = valid_dates.min()
                max_date_val = valid_dates.max()
                
                # Định dạng lại ngày để hiển thị đẹp mắt (dd/mm/yyyy)
                min_date_str = min_date_val.strftime("%d/%m/%Y")
                max_date_str = max_date_val.strftime("%d/%m/%Y")
                
                # Hiển thị khung thông báo
                st.info(f"📂 **Thông tin file:** Các đơn hàng trong file được tạo từ ngày **{min_date_str}** đến ngày **{max_date_str}**.")
            else:
                st.warning("Không tìm thấy dữ liệu ngày tháng hợp lệ trong file.")
                min_date_val = date.today()
                max_date_val = date.today()
            
            # --- BỘ LỌC THỜI GIAN ---
            st.subheader("📅 Lọc dữ liệu theo thời gian")
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("Từ ngày:", min_date_val, format="DD/MM/YYYY")
            with col_d2:
                end_date = st.date_input("Đến ngày:", max_date_val, format="DD/MM/YYYY")

            # Áp dụng lọc theo khoảng thời gian đã chọn
            mask = (summary_table['Ngày chuẩn'] >= start_date) & (summary_table['Ngày chuẩn'] <= end_date)
            filtered_table = summary_table.loc[mask]
            
            if filtered_table.empty:
                st.warning("Không có đơn hàng nào trong khoảng thời gian này.")
            else:
                st.subheader("📋 Bảng Dữ Liệu Thu Gọn")
                # Hiển thị thêm cột % Hoa hồng vào bảng
                st.dataframe(filtered_table[[col_date, col_product, col_status, "GMV đơn hàng", "% Hoa hồng", "Tiền thực nhận (VNĐ)"]], use_container_width=True)
                
                # --- TÍNH TOÁN CÁC CHỈ SỐ ---
                total_orders = len(filtered_table)
                total_gmv = filtered_table["GMV đơn hàng"].sum()
                
                # Tính toán cho các đơn đã quyết toán
                completed_df = filtered_table[filtered_table[col_status].astype(str).str.contains("Đã quyết toán|Hoàn thành|Đã giao", na=False, case=False)]
                completed_orders = len(completed_df)
                completed_money = completed_df["Tiền thực nhận (VNĐ)"].sum()
                
                # --- HIỂN THỊ KẾT QUẢ CHỈ SỐ ---
                st.subheader("💡 Kết quả Tổng hợp (Đã lọc)")
                m1, m2, m3, m4 = st.columns(4)
                
                m1.metric("Tổng số đơn tải lên", f"{total_orders} đơn")
                m2.metric("Tổng GMV bán ra", f"{total_gmv:,.0f} ₫")
                m3.metric("Số đơn Đã quyết toán", f"{completed_orders} đơn")
                m4.metric("Tổng hoa hồng thực nhận", f"{completed_money:,.0f} ₫")
                
                st.divider()
                
                # --- VẼ BIỂU ĐỒ ---
                st.subheader("📈 Biểu đồ Tiền thực nhận theo từng sản phẩm")
                chart_df = completed_df.groupby(col_product)["Tiền thực nhận (VNĐ)"].sum().reset_index()
                chart_df = chart_df.sort_values(by="Tiền thực nhận (VNĐ)", ascending=False)
                
                if not chart_df.empty:
                    st.bar_chart(data=chart_df.set_index(col_product))
                else:
                    st.info("Chưa có đơn đã quyết toán trong khoảng thời gian này để vẽ biểu đồ.")
            
    except Exception as e:
        st.error(f"Có lỗi xảy ra: {e}")