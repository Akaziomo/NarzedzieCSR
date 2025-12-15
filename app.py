import streamlit as st
import pandas as pd
import time


# ----------------------------------------------------------------------
# 0. FUNKCJE POMOCNICZE
# ----------------------------------------------------------------------

def calculate_scores(pytania_df):
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        
        wybrana_opcja_label = st.session_state.get(klucz_pytania)

        if wybrana_opcja_label is not None:
            try:
                punkty_za_odpowiedz_id = row['Opcje_Punkty'][wybrana_opcja_label]
                przypisane_poziomy = row['Przypisanie_Poziomów'][punkty_za_odpowiedz_id]
                
                if isinstance(przypisane_poziomy, list):
                    for poziom in przypisane_poziomy:
                        if poziom in st.session_state.wyniki_poziomow:
                            st.session_state.wyniki_poziomow[poziom] += 1
            except KeyError as e:
                st.error(f"Błąd punktacji dla pytania {row['Pytanie']} i odpowiedzi: {wybrana_opcja_label}. Upewnij się, że odpowiedź istnieje w kluczach.")
                
def go_to_test():
    st.session_state["page"] = "test"
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    st.session_state['validation_error'] = False
    st.session_state['missing_q_numbers'] = []
    
def go_to_welcome():
    st.session_state["page"] = "welcome"

def validate_answers(pytania_df):
    """Sprawdza, czy wszystkie pytania mają wybraną odpowiedź (nie-None) i zapisuje numery brakujących pytań."""
    
    st.session_state['validation_error'] = False
    st.session_state['missing_q_numbers'] = [] 
    
    pytania_bez_odpowiedzi = []
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        wybrana_opcja = st.session_state.get(klucz_pytania)
        
        if wybrana_opcja is None:
            pytania_bez_odpowiedzi.append(row['Pytanie_Nr'])

    if pytania_bez_odpowiedzi:
        st.session_state['validation_error'] = True
        st.session_state['missing_q_numbers'] = pytania_bez_odpowiedzi
        return False
    else:
        st.session_state.update(page="results")
        calculate_scores(pytania_df)
        return True


# ----------------------------------------------------------------------
# 1. DEFINICJA PYTAŃ, PUNKTACJI I OPISÓW POZIOMÓW 
# ----------------------------------------------------------------------

obszar_jednolity = 'Ekonomiczny'

pytania_data = [
    # --- OBSZAR: EKONOMICZNY ---

    ("Jak często odbywają się audyty energetyczne?", 'q_ekon_audyt_e', 
     {'Rzadziej niż co 4 lata': 0, 'Regularnie co 4 lata': 1, 'Częściej niż co 4 lata': 5}, 
     {0: [], 1: [1, 2, 3, 4], 5: [5]}, obszar_jednolity),

    ("Jaka jest dostępność systemu operacyjnego firmy (taboru, maszyn, urządzeń)?", 'q_ekon_dostepnosc', 
     {'Poniżej 90%': 0, '90-95%': 1, 'Powyżej 95%': 5}, 
     {0: [], 1: [1, 2, 3, 4], 5: [5]}, obszar_jednolity),

    ("Jaki procent kapitału firmy jest przeznaczany na inwestycje ekologiczne, wspierające lokalną społeczność, badania lub inne inicjatywy o charakterze społecznym i środowiskowym?", 'q_ekon_kapital_inv', 
     {'0%': 0, 'Poniżej 5%': 1, '5-10%': 3, '10-15%': 4, 'Powyżej 15%': 5}, 
     {0: [], 1: [1, 2], 3: [3], 4: [4], 5: [5]}, obszar_jednolity),

    ("Ile wynosi współczynnik zwrotów lub reklamacji w organizacji?", 'q_ekon_wsp_zwrotow', 
     {'Powyżej 5%': 0, '1-5%': 1, '1-0,5%': 3, 'Poniżej 0,5%': 4}, 
     {0: [], 1: [1, 2], 3: [3], 4: [4, 5]}, obszar_jednolity),

    ("Ile wynosi współczynnik kompletności zleceń (produkty lub usługi) w organizacji?", 'q_ekon_wsp_kompl', 
     {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 5}, 
     {0: [], 1: [1, 2, 3, 4], 5: [5]}, obszar_jednolity),

    ("Ile wynosi współczynnik terminowości zleceń (produkty lub usługi) w organizacji?", 'q_ekon_wsp_term', 
     {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 5}, 
     {0: [], 1: [1, 2, 3, 4], 5: [5]}, obszar_jednolity),

    ("Ile wynosi rentowność firmy rozumiana jako stosunek zysku netto do przychodów ze sprzedaży?", 'q_ekon_rentownosc', 
     {'Poniżej 0%': 0, 'Poniżej 10%': 1, '10-13%': 2, '13-17%': 3, 'Powyżej 17%': 4}, 
     {0: [], 1: [1], 2: [2], 3: [3], 4: [4, 5]}, obszar_jednolity),

    ("Ile wynosi zwrot z inwestycji (ROI) z zielonych inwestycji, rozumiany jako stosunek zysku operacyjnego (lub wartości zatrzymanej) do wartości zainwestowanego kapitału?", 'q_ekon_roi', 
     {'Poniżej 0%': 0, '0-5%': 1, '5-10%': 2, '10-15%': 4, 'Powyżej 15%': 5}, 
     {0: [], 1: [1], 2: [2, 3], 4: [4], 5: [5]}, obszar_jednolity),

    ("Jaki poziom redukcji kosztów operacyjnych został osiągnięty dzięki inicjatywom oszczędnościowym i efektywnościowym (np. termomodernizacja, optymalizacja tras, redukcja zużycia energii)?", 'q_ekon_redukcja_kosztow', 
     {'0% lub poniżej': 0, '0-3%': 1, '3-7%': 2, 'Powyżej 7%': 4}, 
     {0: [], 1: [1], 2: [2, 3], 4: [4, 5]}, obszar_jednolity),

    ("Jaki procent dostawców/detalistów pochodzi z lokalnego otoczenia?", 'q_ekon_lokalni_dostawcy', 
     {'0%': 0, '0-15%': 1, '15-30%': 2, '30-50%': 3, 'Powyżej 50%': 5}, 
     {0: [], 1: [1], 2: [2], 3: [3, 4], 5: [5]}, obszar_jednolity),

    ("Ile wynosi stopień wykorzystania zdolności, rozumiany jako stosunek wykorzystanej zdolności produkcyjnej, magazynowej lub urządzeń do ich nominalnych możliwościi?", 'q_ekon_wykorzystanie_zdolnosci', 
     {'Poniżej 50%': 0, '50-70%': 1, '70-85%': 2, 'Powyżej 85%': 4}, 
     {0: [], 1: [1], 2: [2, 3], 4: [4, 5]}, obszar_jednolity),

    ("Ile wynosi całkowita wartość kar pieniężnych poniesionych przez firmę w związku z nieprzestrzeganiem obowiązujących przepisów i regulacji?", 'q_ekon_kary', 
     {'Powyżej 20 000zł': 0, '5 000-20 000zł': 1, '0-5 000zł': 3, '0zł': 5}, 
     {0: [], 1: [1, 2], 3: [3, 4], 5: [5]}, obszar_jednolity), 

    ("Czy w strukturach firmy istnienieje i funkcjonuje zespół ds. zrównoważonego rozwoju?", 'q_org_zespol_zr', 
     {'Firma nie planuje utworzenia zespołu ds. zrównoważonego rozwoju ani nie podejmuje w tym zakresie żadnych działań.': 0, 
      'Firma deklaruje chęć powołania zespołu ds. zrównoważonego rozwoju lub posiada wstępne plany jego utworzenia.': 1, 
      'Tak, zespół opracowuje, testuje oraz wdraża strategię zrównoważonego rozwoju w wybranych obszarach działalności firmy.': 2, 
      'Tak, zespół integruje strategię zrównoważonego rozwoju we wszystkich obszarach funkcjonowania firmy.': 3, 
      'Tak, zespół skutecznie i konsekwentnie realizuje zintegrowaną strategię, która jest w pełni wdrożona, monitorowana i stale doskonalona w całej organizacji.': 4}, 
     {0: [], 1: [1], 2: [2], 3: [3], 4: [4, 5]}, obszar_jednolity),

    ("Jaki jest stosunek firmy do społecznej odpowiedzialności biznesu (CSR)?", 'q_org_stosunek_csr', 
     {'Firma wykazuje ignorancję wobec zasad CSR lub prezentuje wobec nich negatywne nastawienie.': 0, 
      'Zarząd przejawia zainteresowanie tematyką CSR, jednak nie podejmuje jeszcze konkretnych działań.': 1, 
      'Zarząd inicjuje pierwsze działania związane z wdrażaniem zasad CSR w organizacji.': 2, 
      'Firma jest aktywnie zaangażowana w CSR oraz systematycznie wspiera i prowadzi regularne działania w tym obszarze.': 3, 
      'Firma promuje zasady CSR zarówno wewnątrz organizacji, jak i na zewnątrz, traktując je jako integralny element strategii firmy i dobrych praktyk rynkowych.': 5}, 
     {0: [], 1: [1], 2: [2], 3: [3, 4], 5: [5]}, obszar_jednolity),

    ("Jaki jest stosunek firmy do rozwoju i doskonalenia swojej działalności?", 'q_org_doskonalenie', 
     {'Organizacja nie wykazuje zainteresowania rozwojem ani poprawą efektywności swoich działań.': 0, 
      'Pracownicy posiadają świadomość znaczenia trwałego rozwoju oraz podstawowe kompetencje w tym zakresie, jednak nie podejmowane są jeszcze działania praktyczne.': 1, 
      'Prowadzone są testy i badania ukierunkowane na doskonalenie procesów i rozwiązań.': 2, 
      'Organizacja wdraża działania optymalizujące wybrane procesy w celu poprawy efektywności operacyjnej.': 3, 
      'Organizacja działa w oparciu o zasadę ciągłego doskonalenia, regularnie monitorując wyniki i wprowadzając usprawnienia w całym systemie.': 4, 
      'Organizacja działa w oparciu o zasadę ciągłego doskonalenia, regularnie monitorując wyniki i wprowadzając usprawnienia w całym systemie.': 5}, 
     {0: [], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, obszar_jednolity),

    ("Czy zespół wykazuje myślenie strategiczne, kompetencje restrukturyzacyjne i zdolność do samorefleksja?", 'q_org_kompetencje', 
     {'Nie': 0, 'Tak': 2}, 
     {0: [0, 1], 2: [2, 3, 4, 5]}, obszar_jednolity),

    ("Czy odbywa się współpraca z różnymi podmiotami na poziomach regionalnym, krajowym i/lub międzynarodowym w celu doskonalenia zrównoważonych kompetencji?", 'q_org_wspolpraca', 
     {'Nie': 0, 'Tak': 5}, 
     {0: [0, 1, 2, 3, 4], 5: [5]}, obszar_jednolity),

    ("Czy organizacja posiada certyfikat ISO 26000?", 'q_org_iso26000', 
     {'Organizacja nie posiada certyfikatu ISO 26000 ani nie planuje wdrożenia wytycznych tej normy.': 0, 
      'Organizacja nie posiada jeszcze certyfikatu ISO 26000, jednak rozważa jego wdrożenie w przyszłości.': 1, 
      'Organizacja znajduje się w trakcie procesu wdrażania wytycznych normy ISO 26000.': 2, 
      'Organizacja posiada certyfikat ISO 26000 lub w pełni i skutecznie wdrożyła wytyczne tej normy w swojej działalności.': 4}, 
     {0: [], 1: [1], 2: [2, 3], 4: [4, 5]}, obszar_jednolity),
]

pytania_df = pd.DataFrame(
    pytania_data, 
    columns=['Pytanie', 'Klucz', 'Opcje_Punkty', 'Przypisanie_Poziomów', 'Obszar']
)

pytania_df['Pytanie_Nr'] = range(1, len(pytania_df) + 1)
pytania_df['Pytanie_Full'] = pytania_df['Pytanie_Nr'].astype(str) + ". " + pytania_df['Pytanie']


poziomy_nazwy = {
    0: "P0: Brak Formalnego CSR", 
    1: "P1: Wczesny Rozwój", 
    2: "P2: Transformacja", 
    3: "P3: Integracja", 
    4: "P4: Dojrzałość", 
    5: "P5: Innowacyjne Przywództwo"
}

poziomy_opisy = {
    0: "W firmie nie istnieją formalne struktury ani działania mające na celu zarządzanie zrównoważonym rozwojem i CSR. Działania, jeśli występują, są incydentalne i nieskoordynowane. Konieczne jest powołanie zespołu i podjęcie wstępnych działań.",
    1: "Firma ma wstępną świadomość potrzeby działań CSR. Powołano pojedyncze inicjatywy lub zespół, ale brakuje systematyczności i jasno określonych celów. Wskaźniki ekonomiczne i operacyjne są niskie lub na poziomie podstawowym.",
    2: "W firmie rozpoczęto proces formalizacji działań i optymalizacji procesów. Funkcjonuje zespół, a podstawowe wskaźniki efektywności i CSR są monitorowane. Konieczna jest pełna integracja i ukierunkowanie na cele prośrodowiskowe/społeczne.",
    3: "Zrównoważony rozwój jest częściowo zintegrowany z procesami operacyjnymi i celami (np. cele dotyczące rentowności, zwrotów, optymalizacji). Firma osiąga stabilne, choć umiarkowane, wyniki w kluczowych wskaźnikach ekonomicznych i operacyjnych. Czas na zwiększenie inwestycji w zrównoważony rozwój.",
    4: "Dojrzałe zarządzanie CSR. Zrównoważony rozwój jest elementem strategii, a monitoring postępów jest systematyczny. Firma aktywnie dąży do ciągłej poprawy we wskaźnikach ekonomicznych i organizacyjnych (wysoka rentowność, niska awaryjność, wdrożone ISO).",
    5: "Firma jest liderem w dziedzinie zrównoważonej logistyki. Innowacyjne praktyki są integralną częścią działalności. Osiągane są najlepsze wyniki we wszystkich kluczowych wskaźnikach (ponad 99% kompletności/terminowości, wysoka rentowność, pełna współpraca strategiczna). Przekłada się to na przewagę rynkową i budowanie silnej pozycji marki."
}

# ----------------------------------------------------------------------
# 2. INTERFEJS UŻYTKOWNIKA (Streamlit)
# ----------------------------------------------------------------------

if 'page' not in st.session_state:
    st.session_state["page"] = "welcome"

if 'wyniki_poziomow' not in st.session_state:
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0} 

if 'validation_error' not in st.session_state:
    st.session_state['validation_error'] = False
    
if 'missing_q_numbers' not in st.session_state:
    st.session_state['missing_q_numbers'] = []
    
st.set_page_config(page_title="Narzędzie Oceny CSR w Logistyce", layout="wide") 


# --- LOGIKA PRZECHODZENIA MIĘDZY STRONAMI ---

# 1. STRONA POWITALNA
if st.session_state["page"] == "welcome":
    st.title("🌱 Narzędzie Oceny Procesów Logistycznych (CSR)")
    st.header("Witaj w narzędziu do oceny dojrzałości CSR w logistyce!")
    
    st.markdown("""
    To narzędzie zostało stworzone, aby pomóc przedsiębiorstwom logistycznym 
    ocenić aktualny poziom zaangażowania w praktyki zrównoważonego rozwoju (CSR)
    oraz zidentyfikować obszary do poprawy.

    ### Po co ten test?
    1.  **Diagnoza:** Umożliwia szybką ocenę, na którym z 6 Poziomów Dojrzałości 
        (od Poziomu 0: Brak Formalnego CSR, do Poziomu 5: Innowacyjne Przywództwo) 
        znajduje się Twoja firma, na podstawie 18 kryteriów ekonomicznych i organizacyjnych.

    2.  **Rekomendacje:** Na podstawie odpowiedzi otrzymasz ukierunkowane zalecenia 
        dotyczące kolejnych kroków, które pozwolą przejść na wyższy poziom dojrzałości.

    3.  **Edukacja:** Pogłębisz wiedze na temat kluczowych standardów i najlepszych praktyk CSR w Twoim łańcuchu dostaw.

    Proszę odpowiadać na pytania szczerze i zgodnie z aktualnym stanem w firmie.
    """)
    
    st.button("Rozpocznij Ocenę", on_click=go_to_test)
    
    st.markdown("---")
    st.info("""
    **Narzędzie stworzone na potrzeby pracy inżynierskiej na temat:** *Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR*
    
    **Twórcy testu:** Olga Paszyńska, Justyna Robak, Urszula Sewerniuk
    
    **Promotor pracy:** dr inż. Katarzyna Ragin-Skorecka
    """)


# 2. STRONA Z TESTEM
elif st.session_state["page"] == "test":
    
    st.markdown("Proszę odpowiedzieć na poniższe 18 pytań, aby określić poziom dojrzałości CSR.")
    unikalne_obszary = pytania_df['Obszar'].unique()
    
    with st.form("formularz_oceny"):
        for obszar in unikalne_obszary:
            st.header(f"Kryteria: Obszar {obszar}")
            
            df_obszar = pytania_df[pytania_df['Obszar'] == obszar]
            
            for index, row in df_obszar.iterrows():
                st.subheader(f"{row['Pytanie_Full']}")
                
                opcje_do_punktacji = list(row['Opcje_Punkty'].keys())
                klucz_pytania = row['Klucz']
                
                opcje_do_wyswietlenia = opcje_do_punktacji
                initial_index = None
                
                if klucz_pytania in st.session_state and st.session_state[klucz_pytania] in opcje_do_punktacji:
                    try:
                        initial_index = opcje_do_wyswietlenia.index(st.session_state[klucz_pytania])
                    except ValueError:
                        pass
                
                st.radio(
                    "Wybierz odpowiedź:", 
                    opcje_do_wyswietlenia, 
                    key=klucz_pytania,
                    index=initial_index,
                )
        
        if st.session_state.get('validation_error', False):
            missing_q = st.session_state.get('missing_q_numbers', [])
            missing_q_str = ", ".join(map(str, sorted(missing_q)))
            st.error(f"⚠️ Proszę odpowiedzieć na wszystkie pytania. Brakuje odpowiedzi dla pytań o numerach: **{missing_q_str}**.")

        # PRZYCISK ZATWIERDZENIA
        st.form_submit_button(
            "Oblicz Poziom Zrównoważonego Rozwoju",
            on_click=lambda: validate_answers(pytania_df) 
        )

# 3. STRONA Z WYNIKAMI
elif st.session_state["page"] == "results":
    
    st.header("Wynik Oceny i Rekomendacje")
    
    wyniki_poziomow = st.session_state.wyniki_poziomow

    punkty_do_analizy = wyniki_poziomow
    
    if not any(punkty_do_analizy.values()):
        dominujacy_poziom = 0
    else:
        max_punkty_wszystkie = max(punkty_do_analizy.values())
        remisowe_poziomy = [p for p, pkt in punkty_do_analizy.items() if pkt == max_punkty_wszystkie]
        # Wybieramy najniższy poziom w przypadku remisu
        dominujacy_poziom = min(remisowe_poziomy)
    
    st.success(f"**Osiągnięty Poziom Dojrzałości:** {poziomy_nazwy[dominujacy_poziom]}")
    
    # WYJAŚNIENIE OSIĄGNIĘTEGO POZIOMU
    st.markdown(f"**Opis:** {poziomy_opisy[dominujacy_poziom]}")

    st.markdown("---")

    # 1. Tworzenie tabeli z wynikami
    df_wyniki = pd.DataFrame(
        list(wyniki_poziomow.items()), 
        columns=['Poziom_ID', 'Suma Punktów']
    )
    df_wyniki['Poziom'] = df_wyniki['Poziom_ID'].map(poziomy_nazwy)
    df_wyniki = df_wyniki[['Poziom_ID', 'Poziom', 'Suma Punktów']]
    
    # 2. Generowanie Inteligentnego Podsumowania (Wnioski i Rekomendacje)
    st.subheader("Wnioski i Rekomendacje:")
    
    if dominujacy_poziom == 0:
        st.write("Brak formalnych struktur i mierników wskazuje na **brak wdrożonego CSR**. Rekomendacja: Należy jak najszybciej powołać zespół ds. zrównoważonego rozwoju i podjąć wstępne działania, aby osiągnąć **Poziom 1 (Wczesny Rozwój)**.")
    elif dominujacy_poziom == 1:
        st.write("Organizacja wykazuje wstępną świadomość. Rekomendacja: Należy sformalizować działania poprzez testowanie rozwiązań, inicjowanie pierwszych działań CSR oraz dążenie do stabilizacji podstawowych wskaźników operacyjnych, aby osiągnąć **Poziom 2 (Transformacja)**.")
    elif dominujacy_poziom == 2:
        st.write("Powołano zespół i podjęto działania optymalizacyjne. Rekomendacja: Kluczowe jest **zintegrowanie** zrównoważonego rozwoju z celami operacyjnymi (np. wskaźniki zwrotów, ROI) oraz ukierunkowanie zespołu na wdrażanie strategii, aby osiągnąć **Poziom 3 (Integracja)**.")
    elif dominujacy_poziom == 3:
        st.write("Procesy są stabilne, a CSR jest częściowo zintegrowany. Rekomendacja: Należy zwiększyć zaangażowanie finansowe w inwestycje ekologiczne i społeczne, wdrożyć systemową optymalizację procesów oraz uzyskać certyfikaty potwierdzające dojrzałość, aby osiągnąć **Poziom 4 (Dojrzałość)**.")
    elif dominujacy_poziom == 4:
        st.write("Zrównoważony rozwój jest częścią strategii, a wyniki są wysokie. Rekomendacja: Należy dążyć do **Innowacyjnego Przywództwa (Poziom 5)** poprzez maksymalizację wszystkich wskaźników operacyjnych/ekonomicznych (np. >99% terminowości), aktywne promowanie zasad CSR na zewnątrz oraz nawiązanie współpracy na poziomie krajowym/międzynarodowym.")
    elif dominujący_poziom == 5:
        st.write("Gratulacje! Państwa firma jest innowatorem i liderem zrównoważonego rozwoju. Rekomendacja: Kontynuacja działań i wywieranie pozytywnego wpływu na cały łańcuch dostaw i otoczenie.")

    st.markdown("---")

    # 3. Wyświetlenie punktacji w tabeli
    st.subheader("Szczegółowa Tabela Wyników")
    
    # FUNKCJA PODŚWIETLANIA:
    def highlight_dominant_level(row, dominant_level_id):
        is_dominant = row['Poziom_ID'] == dominant_level_id
        return ['background-color: #ffdd44; color: black' if is_dominant else '' for _ in row]
    
    # Wyświetlanie tabeli
    st.dataframe(
        df_wyniki.style.apply(highlight_dominant_level, 
                              axis=1,
                              dominant_level_id=dominujacy_poziom),
        hide_index=True
    )
    
    st.button("Wróć do Pytań / Wykonaj Nową Ocenę", 
              on_click=go_to_test)
    
    st.markdown("---")

    st.markdown(f"""
    ***
    <p style='font-size: 10px; text-align: center;'>
        Narzędzie stworzone na potrzeby pracy inżynierskiej pt. "Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR".<br>
        Autorzy: Olga Paszyńska, Justyna Robak, Urszula Sewerniuk. Promotor: dr inż. Katarzyna Ragin-Skorecka.
    </p>
    """, unsafe_allow_html=True)
