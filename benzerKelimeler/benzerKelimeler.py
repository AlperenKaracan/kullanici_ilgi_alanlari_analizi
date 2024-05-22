#210201096
#Alperen KARACAN
import json
import re
from snowballstemmer import TurkishStemmer
from collections import defaultdict
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import Toplevel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
import networkx as nx

''' Bu Kodda Genel Olarak JSON dosyasından  alınan datalar ile 50 bin kullanıcının ( JSON daki dosyamızdaki kullanıcı sayısından dolayı ) kullanıcıların username,name,takipçi sayısı,takip sayısı,dili,bölgesi,takipçi listesi,takip ettiklerinin listesi tutulmaktadır.
bu veriler ile kullanıcıların ilgi alanlarını bulup txt dosyasına yazdım,İlgi alanlarını bulmak içinde kategorilere ayırarak  txt dosyalarına ayırarak ilgili kategoride kelimeler yazarak bir veri oluşturdum.Sonra da tweetlerde kelimelerin frekansını sayarak elimdeki veriler ile ilgili olup olmadığını kıyasladım
Kıyaslamada da birkaç sorunla karşılaştım karşılaştığım sorunlar : 1- Gereksiz kelimeler(bağlaçlar ve sık kullanılan belli bir anlamı olmayan kelimeler ) onemsiz_words fonksiyonu ile bu sorunu çözdüm.
Yaşadığım 2. Sorun ise kelimelerin hal ekleri veya başka ekleri aldığı durumda birbirlerini farklı kelime olarak algılayıp frekansın yanlış sayılmasıydı bu sorunun çözümü için kelimeleri köklerine ayıran bir snowballstemmer kütüphanesini kullanarak sorunu çözdüm .
Veri setimizde 50 bin kullanıcı olduğu için çalışması 1 saati geçiyordu ve aşırı bellek tüketiyordu onun için reduced data oluşturdum kaç kullanıcı ile çalışmak istiyorsak kodu ona göre güncelleyebiliriz.
Kodun Genel Yapısı budur. Anlattıklarıma ek olarak graph ile görselleştirmede yapılmıştır.
'''


# Türkçe için kök bulucu
stemmer = TurkishStemmer()


def load_and_reduce_json_data(file_path, max_users=100):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Veri setini  kısıtlama
            return data[:max_users]
    except FileNotFoundError:
        print("Dosya Bulunamadı.")
        return []

# Dosya yolu
file_path = 'C:/Users/alper/twitter_data_50K.json'

# JSON verilerini yükleme ve ilk n  kullanıcıyı al
reduced_twitter_data = load_and_reduce_json_data(file_path, 100)

#Kullanici Sinifini Olusturdum
class User:
    def __init__(self, username, name, followers_count, following_count, language, region, tweets, following, followers):
        self.username = username
        self.name = name
        self.followers_count = followers_count
        self.following_count = following_count
        self.language = language
        self.region = region
        self.tweets = tweets
        self.following = following
        self.followers = followers
# Kendi Hash table m ve list node siniflarim
class ListNode:
    """
    Her düğüm, bir anahtar değer çifti ve  'next' referansı içerir.
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

class HashTable:
    """
    Özelleştirilmiş hash tablosu sınıfı.
    Anahtar değer çiftlerini saklamak için
    """
    def __init__(self, size=10):
        self.size = size
        self.table = [None for _ in range(self.size)]  # Hash tablosu, None ile başlayan bir dizi ile başlatılır

    def hash_function(self, key):
        """
        Hash fonksiyonu, bir anahtarın hash değerini hesaplar.
        fonksiyon, anahtarın karakterlerinin ASCII değerlerinin toplamını alır ve tablo boyutuna göre modunu alır.
        """
        return sum(ord(char) for char in key) % self.size

    def insert(self, key, value):
        """
        'insert' metodu, bir anahtar değer çiftini tabloya ekler.
        varsa değeri günceller."""
        index = self.hash_function(key)
        new_node = ListNode(key, value)

        if self.table[index] is None:
            self.table[index] = new_node
        else:
            current = self.table[index]
            while current.next:
                if current.key == key:
                    current.value = value
                    return
                current = current.next
            current.next = new_node

    def search(self, key):
        """
        Eşleşen  değerini döndürür. Yoksa None döndürür.
        """
        index = self.hash_function(key)
        current = self.table[index]

        while current:
            if current.key == key:
                return current.value
            current = current.next
        return None
def turkce_kucuk_harfe_cevir(metin): # Kelimeler İ ile başlarken İ yi okumuyordu o sorunu düzeltmek için ekledim
    harf_ceviri_tablosu = str.maketrans("İI", "iı")
    return metin.translate(harf_ceviri_tablosu).lower()


class Hashmap:
    def __init__(self, size=100):
        self.size = size
        self.data = [None] * self.size

    def _hash_function(self, key):
        return hash(key) % self.size

    def put(self, key, value):
        index = self._hash_function(key)
        if not self.data[index]:
            self.data[index] = []
        for item in self.data[index]:
            if item[0] == key:
                item[1] = value
                return
        self.data[index].append([key, value])

    def get(self, key):
        index = self._hash_function(key)
        if self.data[index]:
            for item in self.data[index]:
                if item[0] == key:
                    return item[1]
        return None

    def items(self):
        all_items = []
        for item_list in self.data:
            if item_list:
                for item in item_list:
                    all_items.append((item[0], item[1]))
        return all_items

# Bubble sorta ek olarak merge sort ve pythonun yerleşik sortunu da denedim arada perfonmans olarak pek fark olmadığı için bubble sortu tercih ettim ama duruma göre diğer algoritmaları kullanabiliriz.

def bubble_sort(items):
    n = len(items)
    for i in range(n):
        for j in range(0, n-i-1):
            if items[j][1] < items[j+1][1]:
                items[j], items[j+1] = items[j+1], items[j]
    return items

def analyze_tweets(tweets, onemsiz_words):
    word_freq = Hashmap()

    for tweet in tweets:
        words = [stemmer.stemWord(word) for word in re.findall(r'\b\w+\b', turkce_kucuk_harfe_cevir(tweet))]
        for word in words:
            if word not in onemsiz_words:
                freq = word_freq.get(word)
                if freq:
                    word_freq.put(word, freq + 1)
                else:
                    word_freq.put(word, 1)

    sorted_words = bubble_sort(word_freq.items())
    return sorted_words[:5]
onemsiz_words = {"olarak","büyük","küçük","altı","üstü","boyunca","yaparak","ilgili","değil","değildir","arasında","sonra","aynı","benzer","yeni","eski","oldukça","ise","ayrıca","bir","gibi", "ve","veya","de", "da", "bu","bunlar","çok", "ile", "için", "ama","en", "mi", "ne", "o", "var","yok", "daha", "kadar", "senin", "benim", "onun"}

def kelimeleri_dosyadan_oku(dosya_yolu):
    kelimeler = []
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
            kelimeler = [satir.strip().lower() for satir in dosya if satir.strip()]  # kelimeleri kücük hale getirip büyük kücük harf hassasiyetini kaldırdım
    except FileNotFoundError:
        print(f"{dosya_yolu} dosyası bulunamadı.")
    return kelimeler
ilgi_alanlari = {
    "Oyun": kelimeleri_dosyadan_oku("Kelimeler/oyun.txt"),
    "Müzik": kelimeleri_dosyadan_oku("Kelimeler/müzik.txt"),
    "Siyasi": kelimeleri_dosyadan_oku("Kelimeler/siyaset.txt"),
    "Teknoloji": kelimeleri_dosyadan_oku("Kelimeler/teknoloji.txt"),
    "Eğlence": kelimeleri_dosyadan_oku("Kelimeler/eglence.txt"),
    "Moda": kelimeleri_dosyadan_oku("Kelimeler/modagiyim.txt"),
    "Edebiyat": kelimeleri_dosyadan_oku("Kelimeler/edebiyat.txt"),
    "Kültür": kelimeleri_dosyadan_oku("Kelimeler/kültür.txt"),
    "Astronomi": kelimeleri_dosyadan_oku("Kelimeler/astronomi.txt"),
    "Yemek ve Mutfak": kelimeleri_dosyadan_oku("Kelimeler/yemek.txt"),
    "Sağlık": kelimeleri_dosyadan_oku("Kelimeler/sağlık.txt"),
    "Sanat": kelimeleri_dosyadan_oku("Kelimeler/sanat.txt"),
    "Tarih": kelimeleri_dosyadan_oku("Kelimeler/tarih.txt"),
    "Spor": kelimeleri_dosyadan_oku("Kelimeler/spor.txt")
}



def kategorize_et_ve_kelime_getir(kelime_listesi, ilgi_alanlari):
    kategori_en_yuksek_kelime = {}

    for kelime,frekans in kelime_listesi:

        for kategori, anahtar_kelimeler in ilgi_alanlari.items():
            if kelime in anahtar_kelimeler:

                if kategori in kategori_en_yuksek_kelime:
                    # Mevcut kategoride daha yüksek frekansa sahip bir kelime varsa güncelleme kısmı
                    if frekans > kategori_en_yuksek_kelime[kategori][1]:
                        kategori_en_yuksek_kelime[kategori] = (kelime, frekans)
                else:
                    kategori_en_yuksek_kelime[kategori] = (kelime, frekans)
                    break


    return kategori_en_yuksek_kelime

# Kullanıcının ilgi alanlarını kategorize edelim
def dfs_tweets(user, keywords):
    def dfs(tweet_list, index):
        if index == len(tweet_list):
            return []

        tweets_found = []
        tweet = tweet_list[index]
        if any(keyword in tweet for keyword in keywords):
            tweets_found.append(tweet)

        return tweets_found + dfs(tweet_list, index + 1)

    return dfs(user.tweets, 0)

def kullanici_secimi_ve_analizi(kullanicilar):
    while True:
        toplam_kullanici_sayisi = len(kullanicilar)
        secim = int(
            input(f"Hangi kullanıcının analizini almak istersiniz? (1 - {toplam_kullanici_sayisi}, Çıkmak ve kullanıcı graphını açmak için -1): "))

        if secim == -1:
            print("Çıkış yapılıyor...")
            break

        if 1 <= secim <= toplam_kullanici_sayisi:
            secilen_kullanici_json = kullanicilar[secim - 1]
            secilen_kullanici = User(
                username=secilen_kullanici_json["username"],
                name=secilen_kullanici_json["name"],
                followers_count=secilen_kullanici_json["followers_count"],
                following_count=secilen_kullanici_json["following_count"],
                language=secilen_kullanici_json["language"],
                region=secilen_kullanici_json["region"],
                tweets=secilen_kullanici_json["tweets"],
                following=secilen_kullanici_json["following"],
                followers=secilen_kullanici_json["followers"]
            )

            print(f"\nKullanıcı Adı: {secilen_kullanici.username}")
            print(f"Adı: {secilen_kullanici.name}")
            print(f"Takipçi Sayısı: {secilen_kullanici.followers_count}")
            print(f"Takip Ettiği Kişi Sayısı: {secilen_kullanici.following_count}")
            print(f"Dil: {secilen_kullanici.language}")
            print(f"Bölge: {secilen_kullanici.region}")

            tweet_analysis_result = analyze_tweets(secilen_kullanici.tweets, onemsiz_words)
            kullanici_ilgi_alanlari_ve_kelimeleri = kategorize_et_ve_kelime_getir(tweet_analysis_result, ilgi_alanlari)
            # İlgi alanlarını ve ilgili kelimeleri yazdır
            print("\nKullanıcının İlgi Alanları ve İlgili Kelimeler:")
            for kategori, (kelime, frekans) in kullanici_ilgi_alanlari_ve_kelimeleri.items():
                print(f"İlgili Kategori: {kategori}, İlgili Kelime: {kelime},Kelimenin Frekansı: {frekans}")

            print("\nEn Çok Kullanılan İlk 5 Kelime:")
            for kelime, frekans in tweet_analysis_result:
                print(f"{kelime}: {frekans}")

        else:
            print("Geçersiz seçim. Lütfen geçerli bir numara giriniz.")

    # Kullanıcı seçimi ve analizi yapmak için bu fonksiyonu çağırın

def grupla_kullanici_ilgi_alanlari(kullanici_ilgi_alanlari):
    ilgi_alani_kullanici_gruplari = defaultdict(list)
    for kullanici, ilgi_alanlari in kullanici_ilgi_alanlari.items():
        for ilgi_alani in ilgi_alanlari.keys():
            ilgi_alani_kullanici_gruplari[ilgi_alani].append(kullanici)
    return ilgi_alani_kullanici_gruplari

def benzer_kullanicilari_bul_ve_kaydet(kullanici_ilgi_alanlari, dosya_adi):

    kullanici_index_dict = {kullanici: index for index, kullanici in enumerate(kullanici_ilgi_alanlari, start=1)}

    with open(dosya_adi, 'w', encoding='utf-8') as dosya:
        for kullanici_index, (kullanici, ilgi_alanlari) in enumerate(kullanici_ilgi_alanlari.items(), start=1):
            benzer_kullanicilar = []

            for benzerk, benzerk_ilgi_alanlari in kullanici_ilgi_alanlari.items():
                if kullanici != benzerk:
                    ortak_ilgi_alanlari = set(ilgi_alanlari.keys()) & set(benzerk_ilgi_alanlari.keys())
                    if ortak_ilgi_alanlari:
                        # Benzer kullanıcının indeksini bul ve ekle
                        benzerk_index = kullanici_index_dict[benzerk]
                        benzer_kullanicilar.append(f"{benzerk_index}. {benzerk}")

            if benzer_kullanicilar:
                dosya.write(f"\n{kullanici_index}. Kullanıcı: {kullanici} ile ortak ilgi alanlarına sahip kullanıcılar: {', '.join(benzer_kullanicilar)}\n")


def kullanici_ilgi_alanlarini_analiz_et(kullanicilar):
    kullanici_ilgi_alanlari = {}
    for kullanici in kullanicilar:
        usero = User(
            username=kullanici["username"],
            name=kullanici["name"],
            followers_count=kullanici["followers_count"],
            following_count=kullanici["following_count"],
            language=kullanici["language"],
            region=kullanici["region"],
            tweets=kullanici["tweets"],
            following=kullanici["following"],
            followers=kullanici["followers"]
        )
        tweet_analysis_result = analyze_tweets(usero.tweets, onemsiz_words)
        ilgi_alanlari_result = kategorize_et_ve_kelime_getir(tweet_analysis_result, ilgi_alanlari)
        kullanici_ilgi_alanlari[kullanici['username']] = ilgi_alanlari_result
    return kullanici_ilgi_alanlari

# Kullanıcı grafiğini çizme fonksiyonu
def draw_user_graph(user_index):
    # Yeni bir pencere oluştur ve bu pencerede grafiği göster
    new_window = Toplevel(window)
    new_window.title(f"Kullanıcı Grafiği - {user_index}")
    new_window.state('zoomed')  # Tam ekran
    # Frame oluştur
    frame = tk.Frame(new_window)
    frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Grafiği oluştur
    G = nx.DiGraph()

    # Kullanıcı indeksine göre kullanıcıyı ve onun ilişkilerini grafa ekleme işlemi
    if 0 <= user_index < len(reduced_twitter_data):
        user = reduced_twitter_data[user_index]
        username = user["username"]
        G.add_node(username)
        for followed in user.get("following", []):
            G.add_node(followed)
            G.add_edge(username, followed)

    # Yerleştirme algoritması
    pos = nx.spring_layout(G, k=0.5, iterations=100)  # k, itme çekme k artarsa doğru itme mesafesine yaklaşılır ama artması kodu yavaşlatır
    # Figure nesnesi oluştur
    fig = plt.Figure(figsize=(15, 15))
    ax = fig.add_subplot(111)

    # Grafiği  çizme
    nx.draw(G, pos, ax=ax, with_labels=True, node_color='blue', node_size=50, font_size=9)

    # Grafiği Tkinterda gösterme
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Navigation toolbar ekledim ama bir faydası göremedim fakat graph çiziminde sorun olmadığı için akışta bir sıkıntı yok
    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)

    new_window.mainloop()




window = tk.Tk()
window.title("Kullanıcı Grafiği")


label = tk.Label(window, text="Kullanıcı Indeksi (0'dan başlayarak):")
label.grid(row=0, column=0)

entry = tk.Entry(window)
entry.grid(row=0, column=1)

draw_button = tk.Button(window, text="Grafiği Çiz", command=lambda: draw_user_graph(int(entry.get())))
draw_button.grid(row=0, column=2)

kullanici_ilgi_alanlari = kullanici_ilgi_alanlarini_analiz_et(reduced_twitter_data)
benzer_kullanicilari_bul_ve_kaydet(kullanici_ilgi_alanlari, "benzer_ilgi_alanlari.txt")
kullanici_secimi_ve_analizi(reduced_twitter_data)

if __name__ == "__main__":
    # Grafiği oluşturmak ve göstermek için fonksiyonu çağırmak graphı başlat
    window.mainloop()