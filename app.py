import streamlit as st
import json
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv



load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')


genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json"
}

system_prompt="""
Sen yardımsever bir telekom asistanısın. Müşterilere aşağıdaki dört ana konudan birinde destek sağlamaya odaklanıyorsun:

1-Kalan Haklar: Kullanıcının mevcut tarifesinde kalan internet, dakika ve SMS haklarını göster.
2-Yeni Tarife: Kullanıcı yeni tarifeleri öğrenmek istiyorsa ona mevcut tarifeleri listele.
3-Müşteri Temsilcisi: Kullanıcı müşteri temsilcisiyle görüşmek istiyorsa önce sebebini sor sonra yönlendir.
4-Tarife Fiyatı: Mevcut tarifenin fiyatını söyle.
5-Çıkış:Sohbeti sonlandıran bir cümle ile bitir
Sadece bu sorulara cevap ver
Yapmaman gerekenler:

Alakasız sohbetlere girme veya sorunun dışında konulara odaklanma.
Eğer soru üstteki seçeneklerle ilgisi yoksa 'Ben bir yapay zeka asistanıyım konu dışındaki sorulara cevap veremem' de
Destek sağlamadığınız konulara yanıt verme.

Bunları uygula:

Sadece yukarıdaki seçeneklere odaklanarak kullanıcıların sorularına yanıt ver.
Yardımsever, pozitif bir dil kullan ve empati göster .
Yanıtlarının sonunda cümlenle ilgili pozitif bir emoji ekle.
Eğer kullanıcı müşteri temsilcisine yönlendirilmek istiyorsa önce sebebini sor sonra  nazikçe temsilciye yönlendir.
Örnek Senaryolar:

Kullanıcı:"Yardım edebileceğim herhangi bir konu var mı"
Kullanıcı: "Kalan internet hakkımı nasıl öğrenebilirim?"
Asistan: "Mevcut internet hakkınız 5 GB 😊."

Kullanıcı:"Yardım edebileceğim herhangi bir konu var mı"
Kullanıcı: "Telefonum çekmiyor"
Asistan: "Dilerseniz sizi müşteri temsilcimizle görüşmenizi isterim.! 😊"

Kullanıcı:"Yardım edebileceğim herhangi bir konu var mı"
Kullanıcı: "Müşteri temsilcisiyle görüşmek istiyorum."
Asistan: "Tabii, sizi müşteri temsilcisine yönlendirmeden önce yapmak istediğiniz işlemi kısaca yazar mısınız? 😊."

Kullanıcı:"Yardım edebileceğim herhangi bir konu var mı"
Kullanıcı: "Bana bu tarife yetmiyor"
Asistan: "Hemen  size  uygun tarifeleri getiriyorum! 😊"

Çıktı formatı:
JSON şeması kullan:
json
{"eylem":str,
  "olay":str,
  "olasılık":float
}

* "DUR":Eğer kullanıcının isteğini anladıysan,
Karşılık gelen seçenek numarasına (1-5) sahip olayı döndür.
{"eylem":"DUR",
  "olay":1 //Kalan haklarını göstermek,
  "olasılık":0.74
} // 

"Devam Et":Eğer  cevap vermek için daha fazla bilgiye ihtiyacın varsa bu eylemi döndür,
{"eylem":"CONTINUE",
  "olay":"Yeni tarife fiyatlarını görmek ister misiniz ?"
  "olasılık":0.85
}

* Sohbeti bu şeklde başlat:
{"eylem":"Devam Et"
"olay":"Yardım edebileceğim herhangi bir konu var mı"
"olasılık":1
}
"""


model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=[
        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},
        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
    ],
    system_instruction=system_prompt
)
chat = model.start_chat(history=[])

class Customer:
    def __init__(self):
        self.kalan_haklari = "500 dk 10 gb 225 sms hakkınız kalmıştır"
        self.tarife_fiyati = "Tarifeniz 250tl dir"
        self.musteri_temsilcisi = "müşteri temsilci numarası=333 333 33 33"
        self.en_uygun_tarife = "1000 dk 20 gb 500 sms sadece 500tldir"

    def kalan_haklarini_goster(self):
        return f"Kalan haklarınız: {self.kalan_haklari}"

    def yeni_tarife_bilgisi(self):
        return f"En uygun tarife aranıyor....\n{self.en_uygun_tarife} Bu tarifeye geçmek istermisniz?"

    def musteri_temsilcisine_yonlendir(self):
        return f"Müşteri temsilcimizle görüşmek için {self.musteri_temsilcisi} numaralı telefonu arayabilirsiniz. 😊"

    def tarife_fiyati_bilgisi(self):
        return f"Tarifenizin fiyatı: {self.tarife_fiyati}"

def chatbot_response(message, customer):
    response_text = ""
    response = chat.send_message(message)
    decision = json.loads(response.text)

    if decision["eylem"] == "Devam Et" or decision["olasılık"] < 0.7:
        response_text = decision["olay"]
    else:
        choice = (decision["olay"])
        if choice == 1:
            response_text = customer.kalan_haklarini_goster()
        elif choice == 2:
            response_text = customer.yeni_tarife_bilgisi()
        elif choice == 3:
            response_text = customer.musteri_temsilcisine_yonlendir()
        elif choice == 4:
            response_text = customer.tarife_fiyati_bilgisi()
        elif choice == 5:
            response_text = "Görüşmek Üzere!"
        else:
            response_text = "Ben bir yapay zeka asistanıyım konu dışındaki sorulara cevap veremem😊."
        

    return response_text

#interface


st.title("TELEBOT")

if "history" not in st.session_state:
    st.session_state.history = []

customer = Customer()


user_input = st.text_input("Sormak istediğiniz bir şeyi buraya yazın:")

if st.button("Gönder") and user_input:
    response = chatbot_response(user_input, customer)
    st.session_state.history.append(("Kullanıcı:", user_input))
    st.session_state.history.append(("Asistan:", response))

for sender, message in st.session_state.history:
    st.write(f"**{sender}** {message}")
