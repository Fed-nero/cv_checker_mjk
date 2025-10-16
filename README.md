# cv_checker_mjk

AI CV Novērtētājs (Gemini Flash 2.5 + Python)
Par projektu

Šī Python programma salīdzina darba aprakstu (JD) ar vairākiem CV, lai novērtētu kandidātu atbilstību.
Rezultātā tiek ģenerēts:

JSON fails katram CV (punkti, stiprās puses, trūkstošās prasmes, vērtējums)

Markdown un HTML pārskats ar kopsavilkumu

Strādā gan ar Gemini API, gan bez tā (fallback režīms ar lokālu analīzi).

Prasības

Python 3.11 vai jaunāks

macOS / Windows / Linux

Komanda:

pip install -r requirements.txt

Lietošana

# 1. Aktivizē virtuālo vidi

source .venv/bin/activate

# 2. (pēc izvēles) Ievadi Gemini API atslēgu

export GOOGLE_API_KEY="tava_atslēga"

# 3. Palaid programmu

python main.py

Rezultāti tiks saglabāti mapē:

outputs/
cv1.txt.json
cv2.txt.json
cv3.txt.json
CV_report.md
CV_report.html

Mapju struktūra
sample_inputs/ # ievaddati – JD un CV faili  
llm_providers/ # Gemini pieslēgums  
outputs/ # ģenerētie rezultāti  
schemas.py # JSON struktūras apraksts  
prompt.md # sistēmas instrukcija  
main.py # galvenais skripts

Gemini API iestatīšana

API atslēgu var iegūt šeit:
https://aistudio.google.com/app/apikey

Un terminālī ievadīt:

export GOOGLE_API_KEY="tava_atslēga"
