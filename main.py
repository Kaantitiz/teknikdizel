import streamlit as st

# Ana sayfa tasarımı
def main():
    st.set_page_config(page_title="Araç Hareket Analizi", page_icon="🚗", layout="wide")
    
    st.markdown("<h1 style='text-align: center;'>Araç Hareket Analizi ve Harita Görselleştirme</h1>", unsafe_allow_html=True)
    
    # Üç kutu oluştur (3. kutu e-posta gönderim için)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #4CAF50; border-radius: 10px;'>
                <h2>Excel Yükleme</h2>
                <p>Excel dosyasını yükleyip yeni bir Excel dosyası oluşturun.</p>
                <a href="/excel_yukleme" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;'>
                        Excel Yükleme
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #008CBA; border-radius: 10px;'>
                <h2>Harita Oluşturma</h2>
                <p>Excel dosyasından harita oluşturun.</p>
                <a href="/harita_olusturma" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #008CBA; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;'>
                        Harita Oluşturma
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #f44336; border-radius: 10px;'>
                <h2>E-Posta Gönder</h2>
                <p>Excel'den toplu e-posta gönderimi yapın.</p>
                <a href="/mail_gonder" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #f44336; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;'>
                        E-Posta Gönder
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
            <div style='text-align: center; padding: 20px; border: 2px solid #9C27B0; border-radius: 10px;'>
                <h2>Satış Analizi</h2>
                <p>Satış performansına göre hedef ve prim belirleyin.</p>
                <a href="/Satis_Analizi" target="_self" style='text-decoration: none; color: white;'>
                    <button style='background-color: #9C27B0; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;'>
                        Satış Analizi
                    </button>
                </a>
            </div>
        """, unsafe_allow_html=True)

# Ana sayfayı çalıştır
if __name__ == "__main__":
    main()
