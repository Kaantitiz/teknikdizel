import streamlit as st

# Ana sayfa tasarımı
def main():
    st.set_page_config(page_title="Araç Hareket Analizi", page_icon="🚗", layout="wide")
    
    st.markdown("<h1 style='text-align: center;'>Araç Hareket Analizi ve Harita Görselleştirme</h1>", unsafe_allow_html=True)
    
    # İki kutu oluştur
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #ccc; border-radius: 10px;'>
                <h2>Excel Yükleme</h2>
                <p>Excel dosyasını yükleyip yeni bir Excel dosyası oluşturun.</p>
                <a href="/excel_yukleme" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;'>
                        Excel Yükleme Sayfasına Git
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #ccc; border-radius: 10px;'>
                <h2>Harita Oluşturma</h2>
                <p>Excel dosyasından harita oluşturun.</p>
                <a href="/harita_olusturma" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;'>
                        Harita Oluşturma Sayfasına Git
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)

# Ana sayfayı çalıştır
if __name__ == "__main__":
    main()