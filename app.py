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

pytania_data = [
    # --- OBSZAR: EKONOMICZNY ---
    #Pytanie 1
    ("Jak często odbywają się audyty energetyczne?", 'q_ekon_audyty_e', 
     {'Rzadziej niż co 4 lata': 0, 'Regularnie co 4 lata': 1, 'Częściej niż co 4 lata': 2}, 
     {0: [0], 1: [3], 2: [5]}, ekonomiczny),

    #Pytanie 2
    ("Jaka jest dostępność systemu operacyjnego firmy (taboru, maszyn, urządzeń)?", 'q_ekon_dostepnosc', 
     {'Poniżej 90%': 0, '90-95%': 1, 'Powyżej 95%': 2}, 
     {0: [0], 1: [3], 2: [5]}, ekonomiczny),
    
    #Pytanie 3
    ("Czy w strukturach firmy istnienieje i funkcjonuje zespół ds. zrównoważonego rozwoju?", 'q_ekon_struktury',
    {'Firma nie planuje utworzenia zespołu ds. zrównoważonego rozwoju ani nie podejmuje w tym zakresie żadnych działań.': 0,
    'Firma deklaruje chęć powołania zespołu ds. zrównoważonego rozwoju lub posiada wstępne plany jego utworzenia.': 1,
    'Tak, zespół opracowuje, testuje oraz wdraża strategię zrównoważonego rozwoju w wybranych obszarach działalności firmy.': 2,
    'Tak, zespół integruje strategię zrównoważonego rozwoju we wszystkich obszarach funkcjonowania firmy.': 3,
    'Tak, zespół skutecznie i konsekwentnie realizuje zintegrowaną strategię, która jest w pełni wdrożona, monitorowana i stale doskonalona w całej organizacji.': 4},
    {0: [0], 1:[1], 2:[2], 3:[4], 4:[5]}, ekonomiczny),

    #Pytanie 4
    ("Jaki jest stosunek firmy do społecznej odpowiedzialności biznesu (CSR)?", 'q_ekon_csr',
    {'Firma wykazuje ignorancję wobec zasad CSR lub prezentuje wobec nich negatywne nastawienie.': 0,
    'Zarząd przejawia zainteresowanie tematyką CSR, jednak nie podejmuje jeszcze konkretnych działań.': 1,
    'Zarząd inicjuje pierwsze działania związane z wdrażaniem zasad CSR w organizacji.': 2,
    'Firma jest aktywnie zaangażowana w CSR oraz systematycznie wspiera i prowadzi regularne działania w tym obszarze.': 3,
    'Firma promuje zasady CSR zarówno wewnątrz organizacji, jak i na zewnątrz, traktując je jako integralny element strategii firmy i dobrych praktyk rynkowych.': 4},
    {0: [0], 1: [1], 2: [2], 3: [4], 4: [5]}, ekonomiczny),

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
    {0: [1], 1: [5]}, ekonomiczny),
    
    #Pytanie 7
    ("Czy odbywa się współpraca z różnymi podmiotami na poziomach regionalnym, krajowym i/lub międzynarodowym w celu doskonalenia zrównoważonych kompetencji?", 'q_ekon_podmioty',
    {'Nie': 0, 'Tak': 1},
    {0: [0], 1: [5]}, ekonomiczny),
    
    #Pytanie 8
    ("Czy organizacja posiada certyfikat ISO 26000?", 'q_ekon_iso',
    {'Organizacja nie posiada certyfikatu ISO 26000 ani nie planuje wdrożenia wytycznych tej normy.': 0,
    'Organizacja nie posiada jeszcze certyfikatu ISO 26000, jednak rozważa jego wdrożenie w przyszłości.': 1,
    'Organizacja znajduje się w trakcie procesu wdrażania wytycznych normy ISO 26000.': 2,
    'Organizacja posiada certyfikat ISO 26000 lub w pełni i skutecznie wdrożyła wytyczne tej normy w swojej działalności.': 3},
    {0: [0], 1: [1], 2:[3], 3:[5]}, ekonomiczny),

    #Pytanie 9
    ("Jaki procent kapitału firmy jest przeznaczany na inwestycje ekologiczne, wspierające lokalną społeczność, badania lub inne inicjatywy o charakterze społecznym i środowiskowym?", 'q_ekon_kapital',
    {'0%': 0, 'Poniżej 5%': 1, '5-9%': 2, '10-15%': 3, 'Powyżej 15%': 4},
    {0: [0], 1: [1], 2: [3], 3: [4], 4: [5]}, ekonomiczny),

    #Pytanie 10
    ("Ile wynosi współczynnik zwrotów lub reklamacji w organizacji?", 'q_ekon_zwrot',
    {'Powyżej 5%': 0, '1-5%': 1, '0,5-0,9%': 2, 'Poniżej 0,5%': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, ekonomiczny),

    #Pytanie 11
    ("Ile wynosi współczynnik kompletności zleceń (produkty lub usługi) w organizacji?", 'q_ekon_kompletnosc',
    {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 2},
    {0: [0], 1: [3], 2: [5]}, ekonomiczny),

    #Pytanie 12
    ("Ile wynosi współczynnik terminowości zleceń (produkty lub usługi) w organizacji?", 'q_ekon_termin',
    {'Poniżej 95%': 0, '95-99%': 1, 'Powyżej 99%': 2},
    {0: [0], 1: [3], 2: [5]}, ekonomiczny),

    #Pytanie 13
    ("Ile wynosi rentowność firmy rozumiana jako stosunek zysku netto do przychodów ze sprzedaży?", 'q_ekon_netto',
    {'0% lub poniżej': 0, 'Poniżej 10% ale więcej niż 0%': 1, '10-13%': 2, '14-17%': 3, 'Powyżej 17%': 4},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [5]}, ekonomiczny),

    #Pytanie 14
    ("Ile wynosi zwrot z inwestycji (ROI) z zielonych inwestycji, rozumiany jako stosunek zysku operacyjnego (lub wartości zatrzymanej) do wartości zainwestowanego kapitału?", 'q_ekon_ROI',
    {'Poniżej 0%': 0, '0-4%': 1, '5-10%': 2, '11-15%': 3, 'Powyżej 15%': 4},
    {0: [0], 1: [1], 2: [2], 3: [4], 4: [5]}, ekonomiczny),

    #Pytanie 15
    ("Jaki poziom redukcji kosztów operacyjnych został osiągnięty dzięki inicjatywom oszczędnościowym i efektywnościowym (np. termomodernizacja, optymalizacja tras, redukcja zużycia energii)?", 'q_ekon_redukcja',
    {'0% lub poniżej': 0, '0-3%': 1, '4-7%': 2, 'Powyżej 7%': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, ekonomiczny),

    #Pytanie 16
    ("Jaki procent dostawców/detalistów pochodzi z lokalnego otoczenia?", 'q_ekon_lokalni',
    {'0%': 0, '0-15%': 1, '16-30%': 2, '31-50%': 3, 'Powyżej 50%': 4},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [5]}, ekonomiczny),

    #Pytanie 17
    ("Ile wynosi stopień wykorzystania zdolności, rozumiany jako stosunek wykorzystanej zdolności produkcyjnej, magazynowej lub urządzeń do ich nominalnych możliwościi?", 'q_ekon_stopien',
    {'Poniżej 50%': 0, '50-70%': 1, '71-85%': 2, 'Powyżej 85%': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, ekonomiczny),

    #Pytanie 18
    ("Ile wynosi całkowita wartość kar pieniężnych poniesionych przez firmę w związku z nieprzestrzeganiem obowiązujących przepisów i regulacji?", 'q_ekon_kary',
    {'Powyżej 20 000zł': 0, '5 001-20 000zł': 1, '1-5 000zł': 2, '0zł': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, ekonomiczny),

    # --- OBSZAR: SPOŁECZNY ---
    #Pytanie 19
    ("Czy w organizacji funkcjonują procedury dotyczące przeciwdziałania dyskryminacji i mobbingowi, obejmujące monitorowanie liczby zgłoszonych incydentów oraz podejmowanie, monitorowanie i raportowanie działań naprawczych?", 'q_ekon_mobbing',
    {'Organizacja nie posiada takowych procedur ani nie planuje ich wdrożenia.': 0,
    'Organizacja deklaruje zamiar opracowania procedur dotyczących przeciwdziałania dyskryminacji i mobbingowi.': 1,
    'Procedury dotyczące przeciwdziałania dyskryminacji i mobbingowi znajdują się w trakcie opracowywania.': 2,
    'Organizacja posiada wdrożone procedury, monitoruje zgłoszone incydenty oraz podejmuje, monitoruje i raportuje działania naprawcze.': 3},
    {0: [0], 1: [1], 2: [2], 3: [5]}, spoleczny),

    #Pytanie 20
    ("W jakim stopniu organizacja dba o dogodne warunki pracy poprzez zapewnianie i promowanie świadczeń pozapłacowych dla pracowników (np. opieka zdrowotna, ubezpieczenie na życie, urlopy rodzicielskie)?", 'q_ekon_swiadczenia',
    {'Organizacja nie analizuje ani nie uwzględnia kwestii świadczeń pozapłacowych jako elementu zapewniania dogodnych warunków pracy.': 0,
    'Organizacja prowadzi działania informacyjne i edukacyjne w zakresie świadczeń pracowniczych, jednak bez spójnej polityki ich stosowania.': 1,
    'Organizacja zapewnia podstawowe świadczenia pozapłacowe pracownikom oraz respektuje standardy dotyczące czasu pracy i odpoczynku.': 2,
    'Organizacja nie tylko stosuje dobre praktyki w zakresie świadczeń i warunków pracy, ale również aktywnie promuje je jako wzór dla innych podmiotów.': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, spoleczny),

    #Pytanie 21
    ("Czy w organizacji realizowane są działania z zakresu wolontariatu pracowniczego i jak często one występują?", 'q_ekon_wolontariat',
    {'Organizacja nie realizuje działań z zakresu wolontariatu pracowniczego ani nie wykazuje zainteresowania ich wdrażaniem.': 0,
    'Organizacja nie prowadzi wolontariatu pracowniczego, jednak deklaruje chęć podjęcia takich działań w przyszłości.': 1,
    'Organizacja okazjonalnie (np. raz w roku na święta) realizuje działania z zakresu wolontariatu pracowniczego.': 2,
    'Organizacja realizuje wolontariat pracowniczy okazjonalnie (więcej niż raz w roku).': 3,
    'Organizacja regularnie i systematycznie realizuje działania z zakresu wolontariatu pracowniczego, aktywnie angażując pracowników.': 4},
    {0: [0], 1: [1], 2: [3], 3: [3], 4: [5]}, spoleczny),

    #Pytanie 22
    ("Jak dostępne dla klientów są informacje o składzie produktu, jego bezpieczeństwie oraz wpływie na środowisko, w tym emisji gazów cieplarnianych, biodegradowalności, możliwości recyklingu i trwałości?", 'q_ekon_sklad',
    {'Takie informacje nie są udostępniane klientom.': 0,
    'Informacje te są dostępne w sposób pośredni lub ograniczony, np. w regulaminach, dokumentach technicznych lub innych źródłach.': 1,
    'Informacje te są łatwo dostępne i jasno komunikowane klientom, np. na stronie internetowej, opakowaniu produktu lub w materiałach informacyjnych.': 2},
    {0: [0,1], 1: [3], 2: [5]}, spoleczny),

    #Pytanie 23
    ("Jaki odsetek partnerów biznesowych stosuje zasady społecznej odpowiedzialności biznesu (CSR), potwierdzone pozytywnym wynikiem audytu etycznego?", 'q_ekon_partner',
    {'Organizacja nie monitoruje stosowania zasad CSR przez współpracujące podmioty.': 0,
    'Organizacja deklaruje zamiar monitorowania partnerów biznesowych pod kątem CSR, jednak nie wdrożyła jeszcze formalnych narzędzi oceny.': 1,
    'Pozytywny wynik audytu etycznego dotyczy mniej niż 20% współpracujących podmiotów.': 2,
    'Pozytywny wynik audytu etycznego dotyczy 20-50% współpracujących podmiotów.': 3,
    'Większość (powyżej 50%) partnerów biznesowych przeszła pozytywny audyt etyczny i stosuje zasady CSR.': 4},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [5]}, spoleczny),

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
    {'0-5 godzin szkoleń na pracownika rocznie.': 0, '6-10 godzin szkoleń na pracownika rocznie.': 1,
    '11-20 godzin szkoleń na pracownika rocznie.': 2, '21-30 godzin szkoleń na pracownika rocznie.': 3,
    '31-40 godzin szkoleń na pracownika rocznie.': 4, 'Powyżej 40 godzin szkoleń na pracownika rocznie.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 26
    ("Jaki procent pracowników podlega regularnym przeglądom wyników pracy oraz rozmowom dotyczącym rozwoju zawodowego i ścieżki kariery?", 'q_ekon_przeglad',
    {'Poniżej 10%': 0, '11-20%': 1, '21-40%': 2, '41-60%': 3, '61-90%': 4, 'Powyżej 90%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 27
    ("Jaki jest poziom najniższego wynagrodzenia w organizacji w relacji do obowiązującej ustawowej płacy minimalnej?", 'q_ekon_wynagrodzenia',
    {'Równe lub niższe od ustawowej płacy minimalnej (≤ 100%).': 0, '100-110% ustawowej płacy minimalnej.': 1,
    '111-130% ustawowej płacy minimalnej.': 2, 'Powyżej 130% ustawowej płacy minimalnej.': 3},
    {0: [0], 1: [1], 2: [3,4], 3: [5]}, spoleczny),

    #Pytanie 28
    ("Jaki procent wynagrodzeń w organizacji jest wypłacany terminowo w stosunku do wszystkich realizowanych wypłat?", 'q_ekon_procent',
    {'Poniżej 90%': 0, '90-94%': 1, '95-97%': 2, '98-100%': 3, '100%': 4},
    {0: [0], 1: [1], 2: [3], 3: [4], 4: [5]}, spoleczny),

    #Pytanie 29
    ("Jaka jest procentowa różnica w wynagrodzeniu podstawowym pomiędzy kobietami a mężczyznami (gender pay gap)?", 'q_ekon_roznica',
    {'Powyżej 20%': 0, '13-20%': 1, '7-12%': 2, '2-6%': 3, 'Poniżej 2%': 4},
    {0: [0], 1: [1], 2: [2], 3: [4], 4: [5]}, spoleczny),

    #Pytanie 30
    ("Jaki procent pracowników organizacji objęty jest układami zbiorowymi pracy lub innymi formalnymi sposobami reprezentacji pracowniczej?", 'q_ekon_uklad',
    {'Poniżej 10%': 0, '10-30%': 1, '31-50%': 2, '51-70%': 3, '71-90%': 4, 'Powyżej 90%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 31
    ("Ile procent z przychodów firmy jest przeznaczane na działania społeczne lub charytatywne (np. darowizny, sponsoring, projekty edukacyjne)?", 'q_ekon_przychody',
    {'Poniżej 0,01%': 0, '0,01-0,05%': 1, '0,06-0,1%': 2, '0,11-0,3%': 3, '0,31-0,5%': 4, 'Ponad 0,5%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, spoleczny),

    #Pytanie 32
    ("Jaki jest wskaźnik rotacji pracowników, rozumiany jako procent odejść pracowników w ciągu roku w stosunku do średniego stanu zatrudnienia?", 'q_ekon_rotacja',
    {'Powyżej 30%': 0, '20-29%': 1, '11-19%': 2, 'Poniżej 10%': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, spoleczny),

    #Pytanie 33
    ("Jaki jest poziom satysfakcji klientów (mierzony np. ankietami) wyrażony jako odsetek klientów zadowolonych lub bardzo zadowolonych?", 'q_ekon_satysfakcja',
    {'Poniżej 50%': 0, '50-65%': 1, '66-75%': 2, '76-85%': 3, 'Powyżej 85%': 4},
    {0: [0], 1: [1], 2: [3], 3: [4], 4: [5]}, spoleczny),

    # --- OBSZAR: ŚRODOWISKOWY ---
    #Pytanie 34
    ("Czy organizacja posiada certyfikat EMAS (Eco-Management and Audit Scheme)?", 'q_ekon_EMAS',
    {'Organizacja nie posiada certyfikatu EMAS ani nie planuje przystąpienia do tego systemu.': 0,
    'Organizacja nie posiada jeszcze certyfikatu EMAS, jednak rozważa jego wdrożenie w przyszłości.': 1,
    'Organizacja znajduje się w trakcie procesu wdrażania systemu EMAS.': 2,
    'Organizacja posiada certyfikat EMAS i skutecznie stosuje jego wymagania w swojej działalności.': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, srodowiskowy),

    #Pytanie 35
    ("Czy organizacja posiada certyfikat ISO 14001?", 'q_ekon_14001',
    {'Organizacja nie posiada certyfikatu ISO 14001 ani nie planuje wdrożenia wytycznych tej normy.': 0,
    'Organizacja nie posiada jeszcze certyfikatu ISO 14001, jednak rozważa jego wdrożenie w przyszłości.': 1,
    'Organizacja znajduje się w trakcie procesu wdrażania wytycznych normy ISO 14001.': 2,
    'Organizacja posiada certyfikat ISO 14001 lub w pełni i skutecznie wdrożyła wytyczne tej normy w swojej działalności.': 3},
    {0: [0], 1: [1], 2: [3], 3: [5]}, srodowiskowy),

    #Pytanie 36
    ("Jak często odbywają się kontrole lub audyty środowiskowe?", 'q_ekon_audyty_czestosc',
    {'Rzadziej niż co 4 lata.': 0, 'Co 4 lata.': 3, 'Co 3 lata.': 4, 'Co 2 lata lub częściej.': 5},
    {0: [0], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 37
    ("Czy firma realizuje działania kompensujące polegające na sadzeniu drzew (samodzielnie lub poprzez współpracę z fundacjami, samorządami lub partnerami zewnętrznymi)?", 'q_ekon_sadzenie_drzew',
    {'Nie, firma nie realizuje żadnych działań związanych z sadzeniem drzew ani kompensacją przyrodniczą.': 0,
    'Jednorazowa lub okazjonalna akcja sadzenia drzew (do 100 drzew rocznie).': 1,
    'Regularne działania (co najmniej raz w roku), obejmujące 101–500 drzew rocznie.': 2,
    'Sadzenie drzew jest elementem polityki CSR lub środowiskowej, firma sadzi 501–2 000 drzew rocznie.': 3,
    'Firma realizuje długofalowy program kompensacji środowiskowej, sadząc 2 001–10 000 drzew rocznie.': 4,
    'Firma sadzi ponad 10 000 drzew rocznie, angażuje pracowników i partnerów biznesowych oraz publicznie raportuje mierzalne efekty.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 38
    ("Jaki procent wszystkich realizowanych dostaw odbywa się z wykorzystaniem transportu kolejowego, wodnego śródlądowego lub rozwiązań intermodalnych (co najmniej jeden ekologiczny środek transportu w łańcuchu dostawy)?", 'q_ekon_transport_intermodal',
    {'0%': 0, '1-5%': 1, '6-15%': 2, '16-30%': 3, '31-50%': 4, 'Powyżej 50%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 39
    ("W jakim stopniu firma ogranicza pobór wody i zamyka obieg wody w procesach czyszczących (np. mycie pojazdów, kontenerów, palet, powierzchni magazynowych), biorąc pod uwagę całkowity pobór wody, całkowity zrzut wody oraz działania w zakresie recyklingu lub ponownego użycia wody?", 'q_ekon_obieg_wody',
    {'Firma nie monitoruje poboru ani zrzutu wody. Cała zużyta woda po procesach czyszczących jest odprowadzana do kanalizacji lub środowiska bez ponownego użycia.': 0,
    'Firma monitoruje całkowity pobór wody, jednak nie stosuje rozwiązań umożliwiających ponowne wykorzystanie wody lub udział wody odzyskanej wynosi do 5%.': 1,
    'Firma wdraża podstawowe rozwiązania oszczędzające wodę (np. separatory, filtry, myjki niskociśnieniowe), a 6–20% wody z procesów czyszczących jest wykorzystywane ponownie.': 2,
    'Firma posiada zorganizowany system obiegu zamkniętego lub półzamkniętego, 21–40% wody jest odzyskiwane i ponownie wykorzystywane': 3,
    'Firma stosuje zaawansowane systemy recyklingu wody (np. wielostopniowa filtracja, oczyszczanie biologiczne) i ponad 41% wody jest ponownie używane.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 5: [5]}, srodowiskowy),

    #Pytanie 40
    ("Czy przy projektowaniu wyrobów oferowanych lub wykorzystywanych przez firmę (np. opakowań, wyposażenia) uwzględnia się zasady ekologicznej konstrukcji, takie jak ograniczanie substancji toksycznych, ułatwiony demontaż, zwiększona trwałość oraz możliwość recyklingu?", 'q_ekon_ecodesign',
    {'Firma nie uwzględnia aspektów ekologicznych przy projektowaniu wyrobów.': 0,
    'Firma uwzględnia podstawowe zasady ekologicznej konstrukcji, jednak bez formalnej polityki (np. wybór trwalszych materiałów, ograniczenie materiałów niebezpiecznych).': 2,
    'Firma posiada formalną politykę lub wytyczne eco-design, a rozwiązania ekologiczne są standardem in projektowaniu większości wyrobów.': 4,
    'Firma projektuje wyroby zgodnie z zaawansowanymi zasadami gospodarki o obiegu zamkniętym (np. modułowość, projektowanie pod ponowne użycie), a dobre praktyki są komunikowane partnerom i klientom.': 5},
    {0: [0], 2: [2], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 41
    ("Jaki procent wyrobów jest wykonywany z materiałów z odzysku, liczony jako stusunek wagi materiałów z recyklingu do całkowitej wagi zużytych materiałów?", 'q_ekon_materialy_z_odzysku',
    {'Poniżej 10%': 0, '10-19%': 1, '20-39%': 2, '40-54%': 3, '55-70%': 4, 'Powyżej 70%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 42
    ("Jaki procent odpadów jest pooddawany recyklingowi?", 'q_ekon_odpady_recykling',
    {'0%': 0, '1%-34%': 1, '35-49%': 2, '50-69%': 3, '70-85%': 4, 'Powyżej 85%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 43
    ("W jaki sposób firma monitoruje, raportuje oraz ogranicza całkowitą emisję gazów cieplarnianych (GHG) z transportu (CO₂, CH₄, N₂O, HFC, PFC, SF₆, NF₃)?", 'q_ekon_emisje_ghg',
    {'Firma nie oblicza ani nie monitoruje emisji GHG z transportu.': 0,
    'Firma oblicza całkowitą emisję GHG z transportu, lecz działania maja charakter tylko sprawozdawczy.': 2,
    'Firma regularnie monitoruje emisję GHG z transportu, analizuje jej zmiany w czasie oraz podejmuje działania ograniczające (np. optymalizacja tras, szkolenia eco-driving).': 4,
    'Firma osiąga mierzalne i systematyczne redukcje emisji GHG z transportu, obejmuje analizą pełen zakres istotnych emisji, wdraża innowacyjne rozwiązania i publicznie raportuje wyniki.': 5},
    {0: [0], 2: [2], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 44
    ("Ile wynosi udział paliw ze źródeł nieodnawialnych (np. olej napędowy, benzyna, LPG) w stosunku do całkowite zużycia paliw w firmie?", 'q_ekon_paliwa_nieodnawialne',
    {'Firma nie monitoruje struktury zużycia paliw lub nie rozróżnia paliw odnawialnych i nieodnawialnych.': 0,
    'Powyżej 95%': 1, '81-95%': 2, '61-80%': 3, '50-60%': 4, 'Poniżej 50%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 45
    ("Czy firma produkuje energię z odnawialnych źródeł (np. fotowoltaika, biomasa, geotermia, wiatr) na potrzeby własnej działalności i jaki był jej udział w całkowitym zużyciu energii?", 'q_ekon_oze_produkcja',
    {'Firma nie monitoruje zużycia energii i nie prowadzi własnej produkcji energii z OZE.': 0,
    'Firma monitoruje zużycie energii, lecz nie produkuje energii z OZE i nie planuje jej uruchomienia.': 1,
    'Firma nie produkuje jeszcze energii z OZE, ale posiada konkretne plany inwestycyjne lub rozpoczęte projekty.': 2,
    'Firma produkuje energię z OZE, która pokrywa do 10% całkowitego zapotrzebowania energetycznego.': 3,
    'Firma produkuje energię z OZE pokrywającą 11–40% zapotrzebowania energetycznego.': 4,
    'Firma produkuje energię z OZE pokrywającą ponad 40% zapotrzebowania energetycznego.': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 46
    ("W jaki sposób firma monitoruje, analizuje i ogranicza całkowitą ilość wytwarzanych odpadów v swojej działalności operacyjnej (transport, magazynowanie, biura, utrzymanie floty)?", 'q_ekon_odpady_monitoring',
    {'Firma nie monitoruje ilości wytwarzanych odpadów i nie posiada danych dotyczących ich całkowitej wagi.': 0,
    'Firma monitoruje całkowitą wagę wytwarzanych odpadów, jednak dane nie są wykorzystywane do planowania działań ograniczających.': 2,
    'Firma regularnie analizuje wagę wytwarzanych odpadów i podejmuje działania mające na celu ich ograniczenie (np. redukcja odpadów opakowaniowych, ponowne użycie materiałów).': 4,
    'Firma systemowo minimalizuje ilość wytwarzanych odpadów, osiąga mierzalne redukcje masy odpadów w czasie oraz wdraża rozwiązania zgodne z gospodarką o obiegu zamkniętym.': 5},
    {0: [0], 2: [2], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 47
    ("Ile wynosi udział pustych przebiegów (przejazdów bez ładunku) w stosunku do całkowitej liczby kilometrów przejechanych przez tabor firmy?", 'q_ekon_puste_przebiegi',
    {'Firma nie monitoruje pustych przebiegów lub ich udział wynosi ponad 40%.': 0,
    '31-40%': 1, '21-30%': 2, '11-20%': 3, '5-10%': 4, 'Poniżej 5%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 48
    ("Jaki procent całkowitego oświetlenia wykorzystywanego w obiektach firmy (magazyny, terminale, biura, place manewrowe) stanowi energooszczędne oświetlenie LED?", 'q_ekon_led_oswietlenie',
    {'Firma nie monitoruje rodzaju stosowanego oświetlenia lub udział oświetlenia LED jest niższy niż 10%.': 0,
    '10-25%': 1, '26-50%': 2, '51-75%': 3, '76-95%': 4, 'Powyżej 95%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 49
    ("Na jakim etapie jest ustanawianie i wdrażanie wymiernych celów, zadań i strategii, by reagować na negatywne skutki dla środowiska związane z działalnością, produktami i usługami przedsiębiorstwa?", 'q_ekon_strategia_cele',
    {'Nie ma planów aby określić i wprowadzić takich celów, zadań i strategii/ nie pracuje się z nimi': 0,
    'Są one określane/ niedługo będą wprowadzane': 1, 'Rozpoczęto ich wprowadzanie': 2,
    'Są świeżo wprowadzone/ niedługo będzie ich pierwsze podsumowanie': 4,
    'Są one ustanowione, wprowadzone, realizowane i regularnie podsumowywane': 5},
    {0: [0], 1: [1], 2: [2], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 50
    ("Czy organizacja identyfikuje i ocenia negatywne skutki dla środowiska związane z jej działalnością, produktami lub usługami?", 'q_ekon_identyfikacja_negatywna',
    {'Nie i nie jest to planowane': 0, 'Nie, ale przygotowanie takiej analizy jest w trakcie': 1,
    'Tak, powstała pierwsza taka analiza/ kiedyś powstała taka analiza, ale jest już nieaktualna': 2,
    'Tak, taka analiza istnieje, jest aktualna i odpowiednio szczegółowa': 5},
    {0: [0], 1: [1], 2: [2], 5: [5]}, srodowiskowy),

    #Pytanie 51
    ("Czy organizacja zapewnienia, wtedy gdy jest to konieczne, odpowiednie działania zaradcze w odpowiedzi na negatywne skutki dla środowiska, powstałe w wyniku działalności przedsiębiorstwa lub do których przedsiębiorstwo się przyczyniło?", 'q_ekon_dzialania_zaradcze',
    {'Nie i nie ma planów aby to wprowadzić': 0, 'Nie, ale jest to w trakcie wprowadzania': 1,
    'Tak, ale od niedawna': 3, 'Tak, za każdym razem': 5},
    {0: [0], 1: [1], 3: [3], 5: [5]}, srodowiskowy),

    #Pytanie 52
    ("Czy przedsiębiorstwo jest zaangażowane we współpracę w ramach środków zaradczych oraz używa siły oddziaływania przedsiębiorstwa w odniesieniu do innych podmiotów powodujących lub przyczyniających się do negatywnych skutków dla środowiska w celu uruchomienia odpowiednich działań zaradczych?", 'q_ekon_wspolpraca_srodowisko',
    {'Nie i nie ma planów aby to wprowadzić': 0, 'Nie, ale jest to w trakcie wprowadzania': 1,
    'Tak, ale od niedawna': 3, 'Tak, większość z tych sytuacji': 4, 'Tak, za każdym razem': 5},
    {0: [0], 1: [1], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 53
    ("Czy organizacja posiada awaryjne plany działania służące zapobieganiu poważnym szkodom dla środowiska i zdrowia wynikającym z działalności przedsiębiorstwa, łagodzeniu takich szkód i ich kontrolowaniu, w tym wypadków i sytuacji awaryjnych, i czy posiada mechanizmy natychmiastowego zgłaszania takich sytuacji właściwym organom?", 'q_ekon_awaryjne_plany',
    {'Nie': 0, 'Tak, ale są one niedokładne lub przestarzałe': 3,
    'Tak i są one aktualne, spisane i dostępne dla osób odpowiedzialnych za wdrożenie takich planów': 5},
    {0: [0], 3: [3], 5: [5]}, srodowiskowy),

    #Pytanie 54
    ("Czy organizacja nieustannie dąży do poprawy efektywności w obszarze ochrony środowiska na poziomie przedsiębiorstwa?", 'q_ekon_ciagla_poprawa',
    {'Nie': 0, 'Jest w trakcie wprowadzania takiego postępowania': 1,
    'Tak, ale nie jest to robione z największym możliwym zaangażowaniem': 3, 'Tak': 5},
    {0: [0], 1: [1], 3: [3], 5: [5]}, srodowiskowy),

    #Pytanie 55
    ("Jaki procent produktów lub usług, które organizacja tworzy i dostarcza nie powoduje nieodpowiedniego oddziaływania na środowisko, jest bezpieczny, jeśli użytkowany zgodnie z przeznaczeniem, jest trwały, i jeśli możliwe nadaje się do naprawy?", 'q_ekon_produkty_bezpieczne',
    {'0-50%': 0, '51-88%': 1, '89-91%': 2, '92-94%': 3, '95-97%': 4, '98-100%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),

    #Pytanie 56
    ("Jaki procent pruduktów może być ponownie wykorzystany, poddany recyklingowi lub bezpiecznie zutylizowany i jest wytwarzany w sposób przyjazny dla środowiska?", 'q_ekon_produkty_oze_recykling',
    {'0-20%': 0, '21-39%': 1, '40-69%': 2, '70-79%': 3, '80-89%': 4, '90-100%': 5},
    {0: [0], 1: [1], 2: [2], 3: [3], 4: [4], 5: [5]}, srodowiskowy),
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
    
    wyniki_poziomow = st.session_state.wyniki_poziomow

    # ----------------------------------------------------------------------
    # LOGIKA OKREŚLANIA DOMINUJĄCEGO POZIOMU
    # ----------------------------------------------------------------------
    
    dominujacy_poziom = 0
    
    if wyniki_poziomow.get(0, 0) > 0:
        dominujacy_poziom = 0

    else:
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

        if osiagniety_poziom_100 > 0:
            dominujacy_poziom = osiagniety_poziom_100
        
        else:
            poziomy_do_testowania_od_1 = [1, 2, 3, 4, 5]
            pierwszy_poziom_z_punktami = 0
            
            for poziom_id in poziomy_do_testowania_od_1:
                aktualne_pkt = wyniki_poziomow.get(poziom_id, 0)
                
                if aktualne_pkt > 0:
                    pierwszy_poziom_z_punktami = poziom_id
                    break
            
            if pierwszy_poziom_z_punktami > 0:
                 dominujacy_poziom = pierwszy_poziom_z_punktami
            else:
                 dominujacy_poziom = 0

    # ----------------------------------------------------------------------
    
    # 1. Tworzenie DataFrame z wynikami
    df_wyniki = pd.DataFrame(
        list(wyniki_poziomow.items()), 
        columns=['Poziom_ID', 'Suma Punktów']
    )
    df_wyniki['Poziom'] = df_wyniki['Poziom_ID'].map(poziomy_nazwy)
    df_wyniki['Procent Osiągnięcia'] = (df_wyniki['Suma Punktów'] / df_wyniki['Poziom_ID'].map(max_punkty_poziomow) * 100).fillna(0).round(1).astype(str) + '%'
    
    df_wyniki = df_wyniki[['Poziom_ID', 'Poziom', 'Suma Punktów', 'Procent Osiągnięcia']]
    
# 2. Generowanie Inteligentnego Podsumowania (Wnioski i Rekomendacje)
    st.header("Wynik Oceny i Rekomendacje")

    if dominujacy_poziom == 0:
        st.error("### Poziom 0: Brak Formalnego CSR")
        st.write("""
        **Analiza:** Firma znajduje się na etapie reaktywnym, gdzie działania prospołeczne i prośrodowiskowe praktycznie nie występują. Brak monitoringu podstawowych wskaźników, takich jak rotacja pracowników czy zużycie mediów, generuje wysokie ryzyko operacyjne.
        
        **Kluczowe Rekomendacje:**
        * **Zarządzanie:** Konieczne jest powołanie zespołu lub wyznaczenie osoby odpowiedzialnej za obszar zrównoważonego rozwoju.
        * **Operacje:** Rozpoczęcie mierzenia podstawowych parametrów, takich jak terminowość i kompletność zleceń, aby ustabilizować fundamenty ekonomiczne.
        * **Standardy:** Wprowadzenie elementarnych procedur antydyskryminacyjnych oraz monitorowanie terminowości wypłat wynagrodzeń.
        """)

    elif dominujacy_poziom == 1:
        st.info("### Poziom 1: Wczesny Rozwój")
        st.write("""
        **Analiza:** Firma posiada wstępną świadomość potrzeby zmian, jednak podejmowane działania mają charakter rozproszony i okazjonalny. Wskaźniki rentowności zielonych inwestycji (ROI) oraz zaangażowanie w wolontariat pozostają na niskim poziomie.
        
        **Kluczowe Rekomendacje:**
        * **Efektywność:** Skupienie się na redukcji pustych przebiegów oraz optymalizacji tras, co pozwoli na szybkie połączenie oszczędności z ochroną środowiska.
        * **Edukacja:** Zwiększenie liczby godzin szkoleń przypadających na jednego pracownika (cel: powyżej 10h rocznie).
        * **Strategia:** Rozważenie wdrożenia wytycznych normy ISO 26000, aby nadać działaniom CSR bardziej formalne ramy.
        """)

    elif dominujacy_poziom == 2:
        st.info("### Poziom 2: Transformacja")
        st.write("""
        **Analiza:** Proces formalizacji działań został rozpoczęty. Firma monitoruje wagę wytwarzanych odpadów oraz zużycie wody, a w strukturach funkcjonuje już dedykowany zespół ds. zrównoważonego rozwoju.
        
        **Kluczowe Rekomendacje:**
        * **Środowisko:** Przejście od pasywnego monitoringu do realnych modernizacji, np. poprzez zwiększenie udziału oświetlenia LED w obiektach powyżej 50%.
        * **Społecznie:** Wdrożenie systematycznych przeglądów wyników pracy oraz rozmów o ścieżkach kariery dla co najmniej 40% personelu.
        * **Łańcuch dostaw:** Rozpoczęcie weryfikacji dostawców pod kątem ich lokalizacji oraz stosowania przez nich zasad etyki biznesowej.
        """)

    elif dominujacy_poziom == 3:
        st.warning("### Poziom 3: Integracja")
        st.write("""
        **Analiza:** Zasady CSR stają się integralną częścią procesów biznesowych. Firma osiąga stabilną rentowność netto (10-13%) i przeznacza wymierną część kapitału na inwestycje prośrodowiskowe.
        
        **Kluczowe Rekomendacje:**
        * **Certyfikacja:** Uzyskanie certyfikatów ISO 14001 lub EMAS, co pozwoli na formalne potwierdzenie dojrzałości środowiskowej przed kontrahentami.
        * **Ekoprojektowanie:** Wdrożenie zasad Eco-designu w odniesieniu do opakowań i procesów logistycznych, przy jednoczesnym zwiększeniu udziału materiałów z odzysku.
        * **HR:** Podjęcie działań na rzecz redukcji luki płacowej (Gender Pay Gap) oraz regularne angażowanie pracowników w wolontariat.
        """)

    elif dominujacy_poziom == 4:
        st.success("### Poziom 4: Dojrzałość")
        st.write("""
        **Analiza:** Firma wykazuje dojrzałe podejście do zarządzania. Wysoka efektywność operacyjna (terminowość >99%) idzie w parze z systemowym monitorowaniem emisji gazów cieplarnianych (GHG).
        
        **Kluczowe Rekomendacje:**
        * **Energia:** Inwestycja we własne odnawialne źródła energii (OZE) z celem pokrycia powyżej 40% zapotrzebowania firmy.
        * **Transport:** Zwiększenie udziału transportu intermodalnego lub niskoemisyjnego w całym łańcuchu dostaw powyżej progu 30%.
        * **Raportowanie:** Wdrożenie pełnej transparentności wyników środowiskowych i społecznych w formie publicznych raportów okresowych.
        """)

    elif dominujacy_poziom == 5: 
        st.success("### Poziom 5: Innowacyjne Przywództwo")
        st.write("""
        **Analiza:** Firma jest liderem i innowatorem w branży logistycznej. Osiągane wyniki, takie jak zerowa wypadkowość, minimalne puste przebiegi (<5%) oraz wysoki zwrot z zielonych inwestycji, stanowią wzorzec rynkowy.
        
        **Kluczowe Rekomendacje:**
        * **Oddziaływanie:** Wywieranie wpływu na partnerów biznesowych poprzez obowiązkowe audyty etyczne i promowanie dobrych praktyk w całym sektorze.
        * **Innowacje:** Współpraca z jednostkami badawczymi nad nowymi technologiami ograniczającymi wpływ logistyki na ekosystem.
        * **Doskonalenie:** Utrzymanie pozycji lidera poprzez stałą aktualizację strategii względem najnowszych globalnych standardów ESG.
        """)
    
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

    # Wyjaśnienie punktacji
    st.markdown("---")
    st.subheader("Jak liczony jest Twój wynik?")
    st.info("""
    Wynik analizy opiera się na modelu dojrzałości procesowej, który ocenia stopień zaangażowania firmy w zrównoważony rozwój według następujących zasad:

    1. Każda udzielona odpowiedź jest przypisana do konkretnych poziomów zaawansowania (P0–P5). System zlicza aktywność firmy w każdym z tych poziomów niezależnie, co pozwala precyzyjnie określić profil organizacji.
    
    2. Procent widoczny w tabeli informuje, w jakim stopniu firma spełnia wymagania danego poziomu w odniesieniu do wszystkich możliwych do podjęcia działań w tym obszarze.
    
    3. * System wskazuje na najwyższy poziom, który firma zrealizowała w **100%**. Świadczy to o pełnej stabilności procesów na danym etapie.
       * Jeśli system zidentyfikuje braki w Poziomie 0 (podstawowe wymogi prawne i etyczne), zostaje on uznany za poziom dominujący. Ma to na celu wskazanie priorytetowych obszarów do naprawy przed dalszym rozwojem.
       * W przypadku braku pełnej realizacji któregokolwiek poziomu, wskazywany jest etap, na którym firma rozpoczęła aktywną transformację.
    """)
    
    # Stopka z podpisami twórców
    st.markdown(f"""
    ***
    <p style='font-size: 10px; text-align: center;'>
        Narzędzie stworzone na potrzeby pracy inżynierskiej pt. "Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR".<br>
        Autorzy: Olga Paszyńska, Justyna Robak, Urszula Sewerniuk. Promotor: dr inż. Katarzyna Ragin-Skorecka.
    </p>
    """, unsafe_allow_html=True)
