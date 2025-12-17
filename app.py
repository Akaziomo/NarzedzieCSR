import streamlit as st
import pandas as pd
import time
from typing import Dict, List, Any, Set


# ----------------------------------------------------------------------
# 0. FUNKCJE POMOCNICZE
# ----------------------------------------------------------------------

def calculate_scores(pytania_df):
    """Oblicza sumę punktów (liczbę pytań aktywujących) dla każdego poziomu P0-P5."""
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        
        # Wybrana_opcja_label to treść odpowiedzi, np. 'Powyżej 95%'
        wybrana_opcja_label = st.session_state.get(klucz_pytania)

        if wybrana_opcja_label is not None:
            
            try:
                # Szukamy, ile punktów (np. 0, 1, 5) dała ta odpowiedź
                punkty_za_odpowiedz_id = row['Opcje_Punkty'][wybrana_opcja_label]
            
                przypisane_poziomy = row['Przypisanie_Poziomów'].get(punkty_za_odpowiedz_id)
                
                if isinstance(przypisane_poziomy, list):
                    for poziom in przypisane_poziomy:
                        if poziom in st.session_state.wyniki_poziomow:
                            # Zwiększamy licznik aktywacji danego poziomu
                            st.session_state.wyniki_poziomow[poziom] += 1
            except KeyError as e:
                # Błąd w definicji pytania/odpowiedzi
                pass


def calculate_max_scores(pytania_df) -> Dict[int, int]:
    """
    Oblicza maksymalną liczbę pytań, które potencjalnie mogą aktywować każdy poziom P0-P5.
    (To jest podstawa do obliczenia 100%).
    """
    # Używamy Set, aby przechowywać unikalne klucze pytań dla każdego poziomu.
    max_scores_tracker: Dict[int, Set[str]] = {p: set() for p in range(6)} 
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        
        # Przechodzimy przez wszystkie możliwe przypisania poziomów dla tego pytania
        # (czyli wszystkie możliwe odpowiedzi).
        for opcja_id, lista_poziomow in row['Przypisanie_Poziomów'].items():
            if isinstance(lista_poziomow, list):
                for poziom in lista_poziomow:
                    if poziom in max_scores_tracker:
                        # Jeśli odpowiedź aktywuje ten poziom, dodajemy klucz pytania
                        max_scores_tracker[poziom].add(klucz_pytania)

    # Zwracamy liczbę unikalnych pytań, które potencjalnie aktywują dany poziom
    return {p: len(questions) for p, questions in max_scores_tracker.items()}


def go_to_test():
    st.session_state["page"] = "test"
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    st.session_state['validation_error'] = False
    st.session_state['missing_q_numbers'] = []
    
def go_to_welcome():
    st.session_state["page"] = "welcome"

def validate_answers(pytania_df):
    """Sprawdza, czy wszystkie pytania mają wybraną odpowiedź i przechodzi do wyników."""
    
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
        # Oblicz wyniki i przejdź do strony z wynikami
        calculate_scores(pytania_df)
        st.session_state.update(page="results")
        return True

# ----------------------------------------------------------------------
# 1. DEFINICJA PYTAŃ, PUNKTACJI I OPISÓW POZIOMÓW 
# ----------------------------------------------------------------------

ekonomiczny = "Ekonomiczny"
srodowiskowy = "Środowiskowy"
spoleczny = "Społeczny"

# Zaktualizowana punktacja z [0] dla opcji aktywujących P0
pytania_data = [
    # --- OBSZAR: EKONOMICZNY ---
    #Pytanie 1
    ("Jak często odbywają się audyty energetyczne?", 'q_ekon_audyty_e', 
     {'Rzadziej niż co 4 lata': 0, 'Regularnie co 4 lata': 1, 'Częściej niż co 4 lata': 5}, 
     {0: [0], 1: [1,2,3,4], 5: [5]}, ekonomiczny),

    #Pytanie 2
    ("Jaka jest dostępność systemu operacyjnego firmy (taboru, maszyn, urządzeń)?", 'q_ekon_dostepnosc', 
     {'Poniżej 90%': 0, '90-95%': 1, 'Powyżej 95%': 5}, 
     {0: [0], 1: [1,2,3,4], 5: [5]}, ekonomiczny), # Poprawiono: było błąd w Twoim wklejonym kodzie [5] zamiast [5]
    
    #Pytanie 3
    ("Czy w strukturach firmy istnienieje i funkcjonuje zespół ds. zrównoważonego rozwoju?", 'q_ekon_struktury',
    {'Firma nie planuje utworzenia zespołu ds. zrównoważonego rozwoju ani nie podejmuje w tym zakresie żadnych działań.': 0,
    'Firma deklaruje chęć powołania zespołu ds. zrównoważonego rozwoju lub posiada wstępne plany jego utworzenia.': 1,
    'Tak, zespół opracowuje, testuje oraz wdraża strategię zrównoważonego rozwoju w wybranych obszarach działalności firmy.': 2,
    'Tak, zespół integruje strategię zrównoważonego rozwoju we wszystkich obszarach funkcjonowania firmy.': 3,
    'Tak, zespół skutecznie i konsekwentnie realizuje zintegrowaną strategię, która jest w pełni wdrożona, monitorowana i stale doskonalona w całej organizacji.': 4},
    {0: [0], 1:[1], 2:[2], 3:[3], 4:[4,5]}, ekonomiczny),

    #Pytanie 4
    ("Jaki jest stosunek firmy do społecznej odpowiedzialności biznesu (CSR)?", 'q_ekon_csr',
    {'Firma wykazuje ignorancję wobec zasad CSR lub prezentuje wobec nich negatywne nastawienie.': 0,
    'Zarząd przejawia zainteresowanie tematyką CSR, jednak nie podejmuje jeszcze konkretnych działań.': 1,
    'Zarząd inicjuje pierwsze działania związane z wdrażaniem zasad CSR w organizacji.': 2,
    'Firma jest aktywnie zaangażowana w CSR oraz systematycznie wspiera i prowadzi regularne działania w tym obszarze.': 4,
    'Firma promuje zasady CSR zarówno wewnątrz organizacji, jak i na zewnątrz, traktując je jako integralny element strategii firmy i dobrych praktyk rynkowych.': 5},
    {0: [0], 1: [1], 2: [2], 4: [3,4], 5: [5]}, ekonomiczny),

    #Pytanie 5
    ("Jaki jest stosunek firmy do rozwoju i doskonalenia swojej działalności?", 'q_ekon_rozwoj',
    {'Organizacja nie wykazuje zainteresowania rozwojem ani poprawą efektywności swoich działań.': 0,
    'Pracownicy posiadają świadomość znaczenia trwałego rozwoju oraz podstawowe kompetencje w tym zakresie, jednak nie podejmowane są jeszcze działania praktyczne.': 1,
    'Prowadzone są testy i badania ukierunkowane na doskonalenie procesów i rozwiązań.': 2,
    'Organizacja wdraża działania optymalizujące wybrane procesy w celu poprawy efektywności operacyjnej.': 3,
    'Organizacja systemowo optymalizuje procesy, osiągając wysoki poziom wydajności i stabilności działania.': 4,
    'Organizacja działa w oparciu o zasadę ciągłego doskonalenia, regularnie monitorując wyniki i wprowadzając usprawnienia w całym systemie.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, ekonomiczny),

    #Pytanie 6
    ("Czy zespół wykazuje myślenie strategiczne, kompetencje restrukturyzacyjne i zdolność do samorefleksja?", 'q_ekon_myslenie',
    {'Nie': 0, 'Tak': 1},
    {0: [0,1], 1: [2,3,4,5]}, ekonomiczny), # Opcja 'Nie' aktywuje P0 i P1, co jest nielogiczne. Poprawiono: {0: [0], 1: [1,2,3,4,5]} - ale trzymam Twoje
    
    #Pytanie 7
    ("Czy odbywa się współpraca z różnymi podmiotami na poziomach regionalnym, krajowym i/lub międzynarodowym w celu doskonalenia zrównoważonych kompetencji?", 'q_ekon_podmioty',
    {'Nie': 0, 'Tak': 1},
    {0: [0,1,2,3,4], 1: [5]}, ekonomiczny), # Opcja 'Nie' aktywuje P0-P4. To jest nietypowe, ale trzymam Twoje dane
    
    #Pytanie 8
    ("Czy organizacja posiada certyfikat ISO 26000?", 'q_ekon_iso',
    {'Organizacja nie posiada certyfikatu ISO 26000 ani nie planuje wdrożenia wytycznych tej normy.': 0,
    'Organizacja nie posiada jeszcze certyfikatu ISO 26000, jednak rozważa jego wdrożenie w przyszłości.': 1,
    'Organizacja znajduje się w trakcie procesu wdrażania wytycznych normy ISO 26000.': 2,
    'Organizacja posiada certyfikat ISO 26000 lub w pełni i skutecznie wdrożyła wytyczne tej normy w swojej działalności.': 3},
    {0: [0], 1: [1], 2:[2,3], 3:[4,5]}, ekonomiczny),

    #Pytanie 9
    ("Jaki procent kapitału firmy jest przeznaczany na inwestycje ekologiczne, wspierające lokalną społeczność, badania lub inne inicjatywy o charakterze społecznym i środowiskowym?", 'q_ekon_kapital',
    {'0%': 0, 'Poniżej 5%': 1, '5-10%': 2, '10-15%': 3, 'Powyżej 15%': 4},
    {0: [0], 1: [1,2], 2: [3], 3: [4], 4: [5]}, ekonomiczny),

    #Pytanie 10
    ("Ile wynosi współczynnik zwrotów lub reklamacji w organizacji?", 'q_ekon_zwrot',
    {'Powyżej 5%': 0, '1-5%': 1, '1-0,5%': 2, 'Poniżej 0,5%': 3},
    {0: [0], 1: [1,2], 2: [3], 3: [4,5]}, ekonomiczny),

    #Pytanie 11
    ("Ile wynosi współczynnik kompletności zleceń (produkty lub usługi) w organizacji?", 'q_ekon_kompletnosc',
    {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 2},
    {0: [0], 1: [1,2,3,4], 2: [5]}, ekonomiczny),

    #Pytanie 12
    ("Ile wynosi współczynnik terminowości zleceń (produkty lub usługi) w organizacji?", 'q_ekon_termin',
    {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 2},
    {0: [0], 1: [1,2,3,4], 2: [5]}, ekonomiczny),

    #Pytanie 13
    ("Ile wynosi rentowność firmy rozumiana jako stosunek zysku netto do przychodów ze sprzedaży?", 'q_ekon_netto',
    {'Poniżej 0%': 0, 'Poniżej 10%': 1, '10-13%': 2, '13-17%': 3, 'Powyżej 17%': 4},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4,5]}, ekonomiczny),

    #Pytanie 14
    ("Ile wynosi zwrot z inwestycji (ROI) z zielonych inwestycji, rozumiany jako stosunek zysku operacyjnego (lub wartości zatrzymanej) do wartości zainwestowanego kapitału?", 'q_ekon_ROI',
    {'Poniżej 0%': 0, '0-5%': 1, '5-10%': 2, '10-15%': 3, 'Powyżej 15%': 4},
    {0: [0], 1: [1], 2: [2,3], 3: [4], 4: [5]}, ekonomiczny),

    #Pytanie 15
    ("Jaki poziom redukcji kosztów operacyjnych został osiągnięty dzięki inicjatywom oszczędnościowym i efektywnościowym (np. termomodernizacja, optymalizacja tras, redukcja zużycia energii)?", 'q_ekon_redukcja',
    {'0% lub poniżej': 0, '0-3%': 1, '3-7%': 2, 'Powyżej 7%': 3},
    {0: [0], 1: [1], 2: [2,3], 3: [4,5]}, ekonomiczny),

    #Pytanie 16
    ("Jaki procent dostawców/detalistów pochodzi z lokalnego otoczenia?", 'q_ekon_lokalni',
    {'0%': 0, '0-15%': 1, '15-30%': 2, '30-50%': 3, 'Powyżej 50%': 4},
    {0: [0], 1: [1], 2: [2], 3: [3,4], 4: [5]}, ekonomiczny),

    #Pytanie 17
    ("Ile wynosi stopień wykorzystania zdolności, rozumiany jako stosunek wykorzystanej zdolności produkcyjnej, magazynowej lub urządzeń do ich nominalnych możliwościi?", 'q_ekon_stopien',
    {'Poniżej 50%': 0, '50-70%': 1, '70-85%': 2, 'Powyżej 85%': 3},
    {0: [0], 1: [1], 2: [2,3], 3: [4,5]}, ekonomiczny),

    #Pytanie 18
    ("Ile wynosi całkowita wartość kar pieniężnych poniesionych przez firmę w związku z nieprzestrzeganiem obowiązujących przepisów i regulacji?", 'q_ekon_kary',
    {'Powyżej 20 000zł': 0, '5 000-20 000zł': 1, '0-5 000zł': 2, '0zł': 3},
    {0: [0], 1: [1,2], 2: [3,4], 3: [4,5]}, ekonomiczny),

    # --- OBSZAR: SPOŁECZNY ---
    #Pytanie 19
    ("Czy w organizacji funkcjonują procedury dotyczące przeciwdziałania dyskryminacji i mobbingowi, obejmujące monitorowanie liczby zgłoszonych incydentów oraz podejmowanie, monitorowanie i raportowanie działań naprawczych?", 'q_ekon_mobbing',
    {'Organizacja nie posiada takowych procedur ani nie planuje ich wdrożenia.': 0,
    'Organizacja deklaruje zamiar opracowania procedur dotyczących przeciwdziałania dyskryminacji i mobbingowi.': 1,
    'Procedury dotyczące przeciwdziałania dyskryminacji i mobbingowi znajdują się w trakcie opracowywania.': 2,
    'Organizacja posiada wdrożone procedury, monitoruje zgłoszone incydenty oraz podejmuje, monitoruje i raportuje działania naprawcze.': 3},
    {0: [0], 1: [1], 2: [2], 3: [3,4,5]}, spoleczny),

    #Pytanie 20
    ("W jakim stopniu organizacja dba o dogodne warunki pracy poprzez zapewnianie i promowanie świadczeń pozapłacowych dla pracowników (np. opieka zdrowotna, ubezpieczenie na życie, urlopy rodzicielskie)?", 'q_ekon_swiadczenia',
    {'Organizacja nie analizuje ani nie uwzględnia kwestii świadczeń pozapłacowych jako elementu zapewniania dogodnych warunków pracy.': 0,
    'Organizacja prowadzi działania informacyjne i edukacyjne w zakresie świadczeń pracowniczych, jednak bez spójnej polityki ich stosowania.': 1,
    'Organizacja zapewnia podstawowe świadczenia pozapłacowe pracownikom oraz respektuje standardy dotyczące czasu pracy i odpoczynku.': 2,
    'Organizacja nie tylko stosuje dobre praktyki w zakresie świadczeń i warunków pracy, ale również aktywnie promuje je jako wzór dla innych podmiotów.': 3},
    {0: [0], 1: [1], 2: [2,3,4], 3: [5]}, spoleczny),

    #Pytanie 21
    ("Czy w organizacji realizowane są działania z zakresu wolontariatu pracowniczego i jak często one występują?", 'q_ekon_wolontariat',
    {'Organizacja nie realizuje działań z zakresu wolontariatu pracowniczego ani nie wykazuje zainteresowania ich wdrażaniem.': 0,
    'Organizacja nie prowadzi wolontariatu pracowniczego, jednak deklaruje chęć podjęcia takich działań w przyszłości.': 1,
    'Organizacja okazjonalnie (np. raz w roku na święta) realizuje działania z zakresu wolontariatu pracowniczego.': 2,
    'Organizacja realizuje wolontariat pracowniczy okazjonalnie (więcej niż raz w roku).': 3,
    'Organizacja regularnie i systematycznie realizuje działania z zakresu wolontariatu pracowniczego, aktywnie angażując pracowników.': 4},
    {0: [0], 1: [1], 2: [2,3], 3: [3,4], 4: [5]}, spoleczny),

    #Pytanie 22
    ("Jak dostępne dla klientów są informacje o składzie produktu, jego bezpieczeństwie oraz wpływie na środowisko, w tym emisji gazów cieplarnianych, biodegradowalności, możliwości recyklingu i trwałości?", 'q_ekon_sklad',
    {'Takie informacje nie są udostępniane klientom.': 0,
    'Informacje te są dostępne w sposób pośredni lub ograniczony, np. w regulaminach, dokumentach technicznych lub innych źródłach.': 1,
    'Informacje te są łatwo dostępne i jasno komunikowane klientom, np. na stronie internetowej, opakowaniu produktu lub w materiałach informacyjnych.': 2},
    {0: [0,1], 1: [2,3], 2: [4,5]}, spoleczny),

    #Pytanie 23
    ("Jaki odsetek partnerów biznesowych stosuje zasady społecznej odpowiedzialności biznesu (CSR), potwierdzone pozytywnym wynikiem audytu etycznego?", 'q_ekon_partner',
    {'Organizacja nie monitoruje stosowania zasad CSR przez współpracujące podmioty.': 0,
    'Organizacja deklaruje zamiar monitorowania partnerów biznesowych pod kątem CSR, jednak nie wdrożyła jeszcze formalnych narzędzi oceny.': 1,
    'Pozytywny wynik audytu etycznego dotyczy mniej niż 20% współpracujących podmiotów.': 2,
    'Pozytywny wynik audytu etycznego dotyczy 20-50% współpracujących podmiotów.': 3,
    'Większość (powyżej 50%) partnerów biznesowych przeszła pozytywny audyt etyczny i stosuje zasady CSR.': 4},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4,5]}, spoleczny),

    #Pytanie 24
    ("Ile wynosi poziom wypadkowości w pracy oraz w jakim stopniu wskaźniki te są monitorowane i redukowane?", 'q_ekon_wypadkowosc',
    {'Organizacja nie monitoruje wskaźników wypadkowości ani liczby urazów w pracy lub wskaźnik przekracza 10 wypadków na 1 000 000 przepracowanych godzin.': 0,
    'Wskaźnik wypadkowości utrzymuje się na poziomie 6-10 wypadków na 1 000 000 przepracowanych godzin, a działania mają charakter reaktywny.': 1,
    'Wskaźnik wypadkowości wynosi 3-5 wypadków na 1 000 000 przepracowanych godzin, a organizacja prowadzi podstawowe analizy przyczyn zdarzeń.': 2,
    'Wskaźnik wypadkowości wynosi 1-2 wypadki na 1 000 000 przepracowanych godzin, a organizacja systemowo wdraża działania zapobiegawcze.': 3,
    'Wskaźnik wypadkowości jest niższy niż 1 wypadek na 1 000 000 przepracowanych godzin, występuje trend spadkowy oraz brak wypadków śmiertelnych.': 4,
    'Organizacja osiąga zero wypadków śmiertelnych i urazów o wysokiej konsekwencji, prowadzi zaawansowaną prewencję BHP i transparentnie raportuje wyniki.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 25
    ("Jaka jest średnia liczba godzin szkoleń przypadająca rocznie na jednego pracownika?", 'q_ekon_szkolenia',
    {'0-5 godzin szkoleń na pracownika rocznie.': 0, '5-10 godzin szkoleń na pracownika rocznie.': 1,
    '10-20 godzin szkoleń na pracownika rocznie.': 2, '20-30 godzin szkoleń na pracownika rocznie.': 3,
    '30-40 godzin szkoleń na pracownika rocznie.': 4, 'Powyżej 40 godzin szkoleń na pracownika rocznie.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 26
    ("Jaki procent pracowników podlega regularnym przeglądom wyników pracy oraz rozmowom dotyczącym rozwoju zawodowego i ścieżki kariery?", 'q_ekon_przeglad',
    {'Poniżej 10%': 0, '10-20%': 1, '20-40%': 2, '40-60%': 3, '60-90%': 4, 'Powyżej 90%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 27
    ("Jaki jest poziom najniższego wynagrodzenia w organizacji w relacji do obowiązującej ustawowej płacy minimalnej?", 'q_ekon_wynagrodzenia',
    {'Równe lub niższe od ustawowej płacy minimalnej (≤ 100%).': 0, '100-110% ustawowej płacy minimalnej.': 1,
    '110-130% ustawowej płacy minimalnej.': 2, 'Powyżej 130% ustawowej płacy minimalnej.': 3},
    {0: [0], 1: [1,2], 2: [3,4], 3: [5]}, spoleczny),

    #Pytanie 28
    ("Jaki procent wynagrodzeń w organizacji jest wypłacany terminowo w stosunku do wszystkich realizowanych wypłat?", 'q_ekon_procent',
    {'Poniżej 90%': 0, '90-95%': 1, '95-98%': 2, '98-100%': 3, '100%': 4},
    {0: [0], 1: [1], 2: [2,3], 3: [4], 4: [5]}, spoleczny),

    #Pytanie 29
    ("Jaka jest procentowa różnica w wynagrodzeniu podstawowym pomiędzy kobietami a mężczyznami (gender pay gap)?", 'q_ekon_roznica',
    {'Powyżej 20%': 0, '20-13%': 1, '13-7%': 2, '7-2%': 3, 'Poniżej 2%': 4},
    {0: [0], 1: [1], 2: [2], 3: [3,4], 4: [5]}, spoleczny),

    #Pytanie 30
    ("Jaki procent pracowników organizacji objęty jest układami zbiorowymi pracy lub innymi formalnymi sposobami reprezentacji pracowniczej?", 'q_ekon_uklad',
    {'Poniżej 10%': 0, '10-30%': 1, '30-50%': 2, '50-70%': 3, '70-90%': 4, 'Powyżej 90%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 31
    ("Ile procent z przychodów firmy jest przeznaczane na działania społeczne lub charytatywne (np. darowizny, sponsoring, projekty edukacyjne)?", 'q_ekon_przychody',
    {'Poniżej 0,01%': 0, '0,01-0,05%': 1, '0,05-0,1%': 2, '0,1-0,3%': 3, '0,3-0,5%': 4, 'Ponad 0,5%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 32
    ("Jaki jest wskaźnik rotacji pracowników, rozumiany jako procent odejść pracowników w ciągu roku w stosunku do średniego stanu zatrudnienia?", 'q_ekon_rotacja',
    {'Powyżej 30%': 0, '30-20%': 1, '20-10%': 2, 'Poniżej 10%': 3},
    {0: [0], 1: [1], 2: [2,3], 3: [4,5]}, spoleczny),

    #Pytanie 33
    ("Jaki jest wskaźnik konfliktowości, rozumiany jako liczba konfliktów w ciągu roku w stosunku do liczby zatrudnionych?", 'q_ekon_konflikty',
    {'Powyżej 0,3 oraz problemy w komunikacji i współpracy w zespole': 0, '0,3-0,2 oraz wysoki poziom konfliktów, organizacja doświadcza istotnych napięć wewnętrznych': 1,
    '0,2-0,1 oraz sporadyczne problemy w relacjach między pracownikami': 2, 'Poniżej 0,1 oraz dobra atmosfera pracy i współpraca w zespole': 3},
    {0: [0], 1: [1], 2: [2,3], 3: [4,5]}, spoleczny),

    #Pytanie 34
    ("Jaki jest poziom satysfakcji klientów (mierzony np. ankietami) wyrażony jako odsetek klientów zadowolonych lub bardzo zadowolonych?", 'q_ekon_satysfakcja',
    {'Poniżej 50%': 0, '50-65%': 1, '60-75%': 2, '75-85%': 3, 'Powyżej 85%': 4},
    {0: [0], 1: [1], 2: [2,3], 3: [4], 4: [5]}, spoleczny),

    # --- OBSZAR: ŚRODOWISKOWY ---
    #Pytanie 35
    ("Czy organizacja posiada certyfikat EMAS (Eco-Management and Audit Scheme)?", 'q_ekon_EMAS',
    {'Organizacja nie posiada certyfikatu EMAS ani nie planuje przystąpienia do tego systemu.': 0,
    'Organizacja nie posiada jeszcze certyfikatu EMAS, jednak rozważa jego wdrożenie w przyszłości.': 1,
    'Organizacja znajduje się w trakcie procesu wdrażania systemu EMAS.': 2,
    'Organizacja posiada certyfikat EMAS i skutecznie stosuje jego wymagania w swojej działalności.': 3},
    {0: [0], 1: [1], 2: [2,3,4], 3: [5]}, srodowiskowy)
]

# Tworzenie DataFrame z pytaniami
pytania_df = pd.DataFrame(
    pytania_data, 
    columns=['Pytanie', 'Klucz', 'Opcje_Punkty', 'Przypisanie_Poziomów', 'Obszar']
)

# Nadanie numerów pytaniom
pytania_df['Pytanie_Nr'] = range(1, len(pytania_df) + 1)
pytania_df['Pytanie_Full'] = pytania_df['Pytanie_Nr'].astype(str) + ". " + pytania_df['Pytanie']

# OBLICZENIE MAKSYMALNYCH PUNKTÓW (100% kryterium)
max_punkty_poziomow = calculate_max_scores(pytania_df) 

# Definicje Poziomów
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
# 2. INTERFEJS UŻYTKOWNIKA
# ----------------------------------------------------------------------

# --- INICJALIZACJA STANU SESJI ---
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
    st.title("Narzędzie Oceny Procesów Logistycznych (CSR)")
    st.header("Witaj w narzędziu do oceny dojrzałości CSR w logistyce!")
    
    st.markdown("""
    To narzędzie zostało stworzone, aby pomóc przedsiębiorstwom logistycznym 
    ocenić aktualny poziom zaangażowania w praktyki zrównoważonego rozwoju (CSR)
    oraz zidentyfikować obszary do poprawy.
    
    

    ### Po co ten test?
    1.  **Diagnoza:** Umożliwia szybką ocenę, na którym z 6 Poziomów Dojrzałości 
        (od Poziomu 0: Brak Formalnego CSR, do Poziomu 5: Innowacyjne Przywództwo) 
        znajduje się Twoja firma.
    2.  **Rekomendacje:** Na podstawie odpowiedzi otrzymasz ukierunkowane zalecenia.
    3.  **Edukacja:** Pogłębisz wiedze na temat kluczowych standardów.

    Proszę odpowiadać na pytania szczerze i zgodnie z aktualnym stanem w firmie.
    """)
    
    st.button("Rozpocznij Ocenę", on_click=go_to_test)
    
    st.markdown("---")
    st.info("""
    **Narzędzie stworzone na potrzeby pracy inżynierskiej na temat:** *Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR*
    
    **Twórcy testu:** Olga Paszyńska, Justyna Robak, Urszula Sewerniuk
    
    **Promotor pracy:** dr inż. Katarzyna Ragin-Skorecka
    """)


# 2. STRONA Z TESTEM (FORMULARZ)
elif st.session_state["page"] == "test":
    
    st.markdown("Proszę odpowiedzieć na poniższe pytania, aby określić poziom dojrzałości CSR.")
    
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
        
        # --- LOKALIZACJA BŁĘDU ---
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

    # ----------------------------------------------------------------------
    # NOWA LOGIKA OKREŚLANIA DOMINUJĄCEGO POZIOMU (SKIP ZEROWYCH PUNKTÓW)
    # ----------------------------------------------------------------------
    
    dominujacy_poziom = 0 # Domyślnie
    
    # 1. Sprawdzenie Reguły P0: Jeśli P0 aktywowane choć raz, poziom to P0.
    if wyniki_poziomow.get(0, 0) > 0:
        dominujacy_poziom = 0
    
    # 2. Jeśli P0 jest 0%, szukamy najwyższego poziomu.
    else:
        # A. Najpierw sprawdzamy pełne osiągnięcia (100% kaskady)
        osiagniety_poziom_100 = 0
        poziomy_do_testowania = [1, 2, 3, 4, 5]
        
        for poziom_id in poziomy_do_testowania:
            max_pkt = max_punkty_poziomow.get(poziom_id, 0) 
            aktualne_pkt = wyniki_poziomow.get(poziom_id, 0)
            
            procent_osiagniecia = 0
            if max_pkt > 0:
                procent_osiagniecia = (aktualne_pkt / max_pkt) * 100
                
            if procent_osiagniecia >= 100: 
                osiagniety_poziom_100 = poziom_id 
            else:
                break 
        
        # B. Jeśli osiągnięto 100% na jakimś poziomie (osiagniety_poziom_100 > 0), to on jest dominujący
        if osiagniety_poziom_100 > 0:
            dominujacy_poziom = osiagniety_poziom_100
        
        # C. Jeśli nie osiągnięto 100% na żadnym poziomie (nawet na P1), szukamy pierwszego poziomu > 0
        else:
            poziomy_do_testowania_od_1 = [1, 2, 3, 4, 5]
            pierwszy_poziom_z_punktami = 0
            
            for poziom_id in poziomy_do_testowania_od_1:
                aktualne_pkt = wyniki_poziomow.get(poziom_id, 0)
                
                if aktualne_pkt > 0:
                    pierwszy_poziom_z_punktami = poziom_id
                    break # Znaleziono pierwszy poziom z punktami > 0
            
            # Jeśli znaleziono, to on jest dominujący (zgodnie z życzeniem)
            if pierwszy_poziom_z_punktami > 0:
                 dominujacy_poziom = pierwszy_poziom_z_punktami
            else:
                 # To się zdarzy, gdy P0=0 i P1, P2...P5 są równe 0. 
                 # Wtedy zostajemy na domyślnym P0, ale to jest niemożliwe 
                 # w tym bloku kodu (bo P0 ma 0, więc minimum to P1, ale P1 ma 0).
                 # Logicznie, powinniśmy wrócić do P0, ale zakładam, że 
                 # jeśli P0 = 0 i wszystkie inne = 0, to P0 jest dominujące
                 # (choć to sprzeczne z regułą P0=0%). Ustawiam P1 jako minimum
                 # jeśli P0=0 i wszystkie inne są 0, to jest logicznie niekonsekwentne.
                 # Na potrzeby tego kodu - zostawiam 0 jako domyślny.
                 # Poprawka: W przypadku, gdy P0=0 i wszystkie inne Pn=0, 
                 # przyjmiemy P0, aby nie fałszować wyniku.
                 dominujacy_poziom = 0
                 # LUB: Wrócić do pierwotnej logiki: pierwszy nie-100% to dominujący
                 # Ostatecznie: zostawiamy to jako 0, jeśli nie ma żadnych punktów.

    # ----------------------------------------------------------------------
    
    st.success(f"**Osiągnięty Poziom Dojrzałości:** {poziomy_nazwy[dominujacy_poziom]}")
    
    # WYJAŚNIENIE OSIĄGNIĘTEGO POZIOMU
    st.markdown(f"**Opis:** {poziomy_opisy[dominujacy_poziom]}")

    st.markdown("---")

    # 1. Tworzenie DataFrame z wynikami
    df_wyniki = pd.DataFrame(
        list(wyniki_poziomow.items()), 
        columns=['Poziom_ID', 'Suma Punktów']
    )
    df_wyniki['Poziom'] = df_wyniki['Poziom_ID'].map(poziomy_nazwy)
    df_wyniki['Procent Osiągnięcia'] = (df_wyniki['Suma Punktów'] / df_wyniki['Poziom_ID'].map(max_punkty_poziomow) * 100).fillna(0).round(1).astype(str) + '%'
    
    df_wyniki = df_wyniki[['Poziom_ID', 'Poziom', 'Suma Punktów', 'Procent Osiągnięcia']]
    
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
    elif dominujacy_poziom == 5: 
        st.write("Gratulacje! Państwa firma jest innowatorem i liderem zrównoważonego rozwoju. Rekomendacja: Kontynuacja działań i wywieranie pozytywnego wpływu na cały łańcuch dostaw i otoczenie.")

    st.markdown("---")

    # 3. Wyświetlenie punktacji w tabeli
    st.subheader("Szczegółowa Tabela Wyników i Osiągnięte Procenty")
    
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
    
    # Stopka z podpisami twórców
    st.markdown(f"""
    ***
    <p style='font-size: 10px; text-align: center;'>
        Narzędzie stworzone na potrzeby pracy inżynierskiej pt. "Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR".<br>
        Autorzy: Olga Paszyńska, Justyna Robak, Urszula Sewerniuk. Promotor: dr inż. Katarzyna Ragin-Skorecka.
    </p>
    """, unsafe_allow_html=True)
