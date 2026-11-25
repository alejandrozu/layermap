# Legitimate groupings that sit above a country's first-level divisions.
# Keys are group names; values are first-level division names (matched accent/case-insensitively).

RUS_FD = {
    'Central': ['Belgorod Oblast', 'Bryansk Oblast', 'Vladimir Oblast', 'Voronezh Oblast', 'Ivanovo Oblast', 'Kaluga Oblast', 'Kostroma Oblast', 'Kursk Oblast', 'Lipetsk Oblast', 'Moscow Oblast', 'Oryol Oblast', 'Ryazan Oblast', 'Smolensk Oblast', 'Tambov Oblast', 'Tver Oblast', 'Tula Oblast', 'Yaroslavl Oblast', 'Moscow'],
    'Northwestern': ['Republic of Karelia', 'Komi Republic', 'Arkhangelsk Oblast', 'Nenets Autonomous Okrug', 'Vologda Oblast', 'Kaliningrad', 'Leningrad oblast', 'Murmansk Oblast', 'Novgorod Oblast', 'Pskov Oblast', 'Saint Petersburg'],
    'Southern': ['Adygea', 'Kalmykia', 'Krasnodar Krai', 'Astrakhan Oblast', 'Volgograd Oblast', 'Rostov Oblast'],
    'North Caucasian': ['Dagestan', 'Ingushetia', 'Kabardino-Balkaria', 'Karachay-Cherkessia', 'North Ossetia–Alania', 'Chechnya', 'Stavropol Krai'],
    'Volga': ['Bashkortostan', 'Mari El', 'Republic of Mordovia', 'Tatarstan', 'Udmurtia', 'Chuvashia', 'Perm Krai', 'Kirov Oblast', 'Nizhny Novgorod Oblast', 'Orenburg Oblast', 'Penza Oblast', 'Samara Oblast', 'Saratov Oblast', 'Ulyanovsk Oblast'],
    'Ural': ['Kurgan Oblast', 'Sverdlovsk Oblast', 'Tyumen Oblast', 'Chelyabinsk Oblast', 'Khanty-Mansiysk Autonomous Okrug – Ugra', 'Yamalo-Nenets Autonomous Okrug'],
    'Siberian': ['Altai Republic', 'Tuva', 'Khakassia', 'Altai Krai', 'Krasnoyarsk Krai', 'Irkutsk Oblast', 'Kemerovo Oblast', 'Novosibirsk Oblast', 'Omsk Oblast', 'Tomsk Oblast'],
    'Far Eastern': ['Sakha Republic', 'Kamchatka Krai', 'Primorsky Krai', 'Khabarovsk Krai', 'Amur Oblast', 'Magadan Oblast', 'Sakhalin Oblast', 'Jewish Autonomous Oblast', 'Chukotka Autonomous Okrug', 'Buryatia', 'Zabaykalsky Krai'],
}
IND_ZONES = {
    'Northern Zonal Council': ['Haryana', 'Himachal Pradesh', 'Punjab', 'Rajasthan', 'Delhi', 'Chandigarh', 'Jammu and Kashmir', 'Ladakh'],
    'Central Zonal Council': ['Chhattisgarh', 'Uttarakhand', 'Uttar Pradesh', 'Madhya Pradesh'],
    'Eastern Zonal Council': ['Bihar', 'Jharkhand', 'Odisha', 'West Bengal'],
    'Western Zonal Council': ['Goa', 'Gujarat', 'Maharashtra', 'Dadra and Nagar Haveli and Daman and Diu'],
    'Southern Zonal Council': ['Andhra Pradesh', 'Karnataka', 'Kerala', 'Tamil Nadu', 'Telangana', 'Puducherry', 'Andaman and Nicobar Islands', 'Lakshadweep'],
    'North Eastern Council': ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura'],
}
CHN_REGIONS = {
    'North China': ['Beijing Municipality', 'Tianjin Municipality', 'Hebei Province', 'Shanxi Province', 'Inner Mongolia Autonomous Region'],
    'Northeast China': ['Liaoning Province', 'Jilin Province', 'Heilongjiang Province'],
    'East China': ['Shanghai Municipality', 'Jiangsu Province', 'Zhejiang Province', 'Anhui Province', 'Fujian Province', 'Jiangxi Province', 'Shandong Province', 'Taiwan Province'],
    'Central China': ['Henan Province', 'Hubei Province', 'Hunan Province'],
    'South China': ['Guangdong Province', 'Guangxi Zhuang Autonomous Region', 'Hainan Province', 'Hong Kong Special Administrative Region', 'Macau Special Administrative Region', 'Macao Special Administrative Region'],
    'Southwest China': ['Chongqing Municipality', 'Sichuan Province', 'Guizhou Province', 'Yunnan Province', 'Tibet Autonomous Region'],
    'Northwest China': ['Shaanxi Province', 'Gansu Province', 'Qinghai Province', 'Ningxia Hui Autonomous Region', 'Xinjiang Uyghur Autonomous Region', 'Xinjiang Uygur Autonomous Region'],
}
MEX_BANXICO = {
    'Norte': ['Baja California', 'Chihuahua', 'Coahuila de Zaragoza', 'Nuevo Leon', 'Sonora', 'Tamaulipas'],
    'Centro Norte': ['Aguascalientes', 'Baja California Sur', 'Colima', 'Durango', 'Jalisco', 'Michoacan de Ocampo', 'Nayarit', 'San Luis Potosi', 'Sinaloa', 'Zacatecas'],
    'Centro': ['Distrito Federal', 'Ciudad de Mexico', 'Mexico', 'Guanajuato', 'Hidalgo', 'Morelos', 'Puebla', 'Queretaro de Arteaga', 'Tlaxcala'],
    'Sur': ['Campeche', 'Chiapas', 'Guerrero', 'Oaxaca', 'Quintana Roo', 'Tabasco', 'Veracruz de Ignacio de la Llave', 'Yucatan'],
}
NGA_ZONES = {
    'North Central': ['Benue', 'Kogi', 'Kwara', 'Nasarawa', 'Niger', 'Plateau', 'Abuja Federal Capital Territory'],
    'North East': ['Adamawa', 'Bauchi', 'Borno', 'Gombe', 'Taraba', 'Yobe'],
    'North West': ['Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Sokoto', 'Zamfara'],
    'South East': ['Abia', 'Anambra', 'Ebonyi', 'Enugu', 'Imo'],
    'South South': ['Akwa Ibom', 'Bayelsa', 'Cross River', 'Delta', 'Edo', 'Rivers'],
    'South West': ['Ekiti', 'Lagos', 'Ogun', 'Ondo', 'Osun', 'Oyo'],
}
JPN_REGIONS = {
    'Hokkaido': ['Hokkaido'],
    'Tohoku': ['Aomori', 'Iwate', 'Miyagi', 'Akita', 'Yamagata', 'Fukushima'],
    'Kanto': ['Ibaraki', 'Tochigi', 'Gunma', 'Saitama', 'Chiba', 'Tokyo', 'Kanagawa'],
    'Chubu': ['Niigata', 'Toyama', 'Ishikawa Prefecture', 'Fukui Prefecture', 'Yamanashi', 'Nagano', 'Gifu Prefecture', 'Shizuoka', 'Aichi Prefecture'],
    'Kansai': ['Mie Prefecture', 'Shiga', 'Kyoto Prefecture', 'Osaka Prefecture', 'Hyogo Prefecture', 'Nara Prefecture', 'Wakayama Prefecture'],
    'Chugoku': ['Tottori Prefecture', 'Shimane', 'Okayama Prefecture', 'Hiroshima', 'Yamaguchi'],
    'Shikoku': ['Tokushima Prefecture', 'Kagawa Prefecture', 'Ehime Prefecture', 'Kochi Prefecture'],
    'Kyushu & Okinawa': ['Fukuoka Prefecture', 'Saga Prefecture', 'Nagasaki Prefecture', 'Kumamoto', 'Oita', 'Miyazaki Prefecture', 'Kagoshima Prefecture', 'Okinawa Prefecture'],
}
THA_REGIONS = {
    'Northern': ['Chiang Mai', 'Chiang Rai', 'Lampang', 'Lamphun', 'Mae Hong Son', 'Nan', 'Phayao', 'Phrae', 'Uttaradit'],
    'Northeastern': ['Amnat Charoen', 'Bueng Kan', 'Buri Ram', 'Chaiyaphum', 'Kalasin', 'Khon Kaen', 'Loei', 'Maha Sarakham', 'Mukdahan', 'Nakhon Phanom', 'Nakhon Ratchasima', 'Nong Bua Lam Phu', 'Nong Khai', 'Roi Et', 'Sakon Nakhon', 'Si Sa Ket', 'Surin', 'Ubon Ratchathani', 'Udon Thani', 'Yasothon'],
    'Western': ['Kanchanaburi', 'Phetchaburi', 'Prachuap Khiri Khan', 'Ratchaburi', 'Tak'],
    'Central': ['Bangkok', 'Ang Thong', 'Phra Nakhon Si Ayutthaya', 'Chai Nat', 'Kamphaeng Phet', 'Lopburi', 'Nakhon Nayok', 'Nakhon Pathom', 'Nakhon Sawan', 'Nonthaburi', 'Pathum Thani', 'Phetchabun', 'Phichit', 'Phitsanulok', 'Samut Prakan', 'Samut Sakhon', 'Samut Songkhram', 'Saraburi', 'Sing Buri', 'Sukhothai', 'Suphan Buri', 'Uthai Thani'],
    'Eastern': ['Chachoengsao', 'Chanthaburi', 'Chon Buri', 'Prachin Buri', 'Rayong', 'Sa Kaeo', 'Trat'],
    'Southern': ['Chumphon', 'Krabi', 'Nakhon Si Thammarat', 'Narathiwat', 'Pattani', 'Phangnga', 'Phatthalung', 'Phuket', 'Ranong', 'Satun', 'Songkhla', 'Surat Thani', 'Trang', 'Yala'],
}
THA_REGIONS = {g: [n + ' Province' for n in v] + v for g, v in THA_REGIONS.items()}
VNM_REGIONS = {
    'Northern Midlands and Mountains': ['Hà Giang', 'Cao Bằng', 'Bắc Kạn', 'Tuyên Quang', 'Lào Cai', 'Yên Bái', 'Thái Nguyên', 'Lạng Sơn', 'Bắc Giang', 'Phú Thọ', 'Điện Biên', 'Lai Châu', 'Sơn La', 'Hòa Bình'],
    'Red River Delta': ['Hà Nội', 'Vĩnh Phúc', 'Bắc Ninh', 'Quảng Ninh', 'Hải Dương', 'Hải Phòng', 'Hưng Yên', 'Thái Bình', 'Hà Nam', 'Nam Định', 'Ninh Bình'],
    'North Central and Central Coast': ['Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Quảng Bình', 'Quảng Trị', 'Thừa Thiên Huế', 'Đà Nẵng', 'Quảng Nam', 'Quảng Ngãi', 'Bình Định', 'Phú Yên', 'Khánh Hòa', 'Ninh Thuận', 'Bình Thuận'],
    'Central Highlands': ['Kon Tum', 'Gia Lai', 'Đắk Lắk', 'Đắk Nông', 'Lâm Đồng'],
    'Southeast': ['Bình Phước', 'Tây Ninh', 'Bình Dương', 'Đồng Nai', 'Bà Rịa–Vũng Tàu', 'Ho Chi Minh', 'Côn Đảo'],
    'Mekong Delta': ['Long An', 'Tiền Giang', 'Bến Tre', 'Trà Vinh', 'Vĩnh Long', 'Đồng Tháp', 'An Giang', 'Kiên Giang', 'Cần Thơ', 'Hậu Giang', 'Sóc Trăng', 'Bạc Liêu', 'Cà Mau'],
}
PHL_ISLANDS = {
    'Luzon': ['NCR', 'CAR', 'Ilocos Region', 'Cagayan Valley', 'Central Luzon', 'Calabarzon', 'Mimaropa', 'Bicol Region'],
    'Visayas': ['Western Visayas', 'Central Visayas', 'Eastern Visayas'],
    'Mindanao': ['Zamboanga Peninsula', 'Northern Mindanao', 'Davao Region', 'Soccsksargen', 'Caraga', 'ARMM'],
}
IDN_ISLANDS = {
    'Sumatra': ['Aceh', 'North Sumatra', 'West Sumatra', 'Riau', 'Riau Islands', 'Jambi', 'South Sumatra', 'Bengkulu', 'Lampung', 'Bangka-Belitung Islands'],
    'Java': ['Banten', 'Jakarta Special Capital Region', 'West Java', 'Central Java', 'Special Region of Yogyakarta', 'East Java'],
    'Lesser Sunda Islands': ['Bali', 'West Nusa Tenggara', 'East Nusa Tenggara'],
    'Kalimantan': ['West Kalimantan', 'Central Kalimantan', 'South Kalimantan', 'East Kalimantan', 'North Kalimantan'],
    'Sulawesi': ['North Sulawesi', 'Gorontalo', 'Central Sulawesi', 'West Sulawesi', 'South Sulawesi', 'Southeast Sulawesi'],
    'Maluku Islands': ['Maluku', 'North Maluku'],
    'Western New Guinea': ['Papua', 'West Papua'],
}
KEN_PROVINCES = {
    'Central': ['Kiambu', 'Kirinyaga', "Murang'a", 'Nyandarua', 'Nyeri'],
    'Coast': ['Kilifi', 'Kwale', 'Lamu', 'Mombasa', 'Taita Taveta', 'Tana River'],
    'Eastern': ['Embu', 'Isiolo', 'Kitui', 'Machakos', 'Makueni', 'Marsabit', 'Meru', 'Tharaka'],
    'North Eastern': ['Garissa', 'Mandera', 'Wajir'],
    'Nairobi': ['Nairobi'],
    'Nyanza': ['Homa Bay', 'Kisii', 'Kisumu', 'Migori', 'Nyamira', 'Siaya'],
    'Rift Valley': ['Baringo', 'Bomet', 'Elgeyo-Marakwet', 'Kajiado', 'Kericho', 'Laikipia', 'Nakuru', 'Nandi', 'Narok', 'Samburu', 'Trans Nzoia', 'Turkana', 'Uasin Gishu', 'West Pokot'],
    'Western': ['Bungoma', 'Busia', 'Kakamega', 'Vihiga'],
}
MDA_REGIONS = {
    'North': ['Balti', 'Briceni', 'Donduseni', 'Drochia', 'Edinet', 'Falesti', 'Floresti', 'Glodeni', 'Ocnita', 'Riscani', 'Singerei', 'Soroca'],
    'Centre': ['Anenii Noi', 'Calarasi', 'Criuleni', 'Dubasari', 'Hincesti', 'Ialoveni', 'Nisporeni', 'Orhei', 'Rezina', 'Straseni', 'Soldanesti', 'Telenesti', 'Ungheni'],
    'South': ['Basarabeasca', 'Cahul', 'Cantemir', 'Causeni', 'Cimislia', 'Leova', 'Stefan Voda', 'Taraclia'],
    'Chișinău': ['Chisinau'],
    'Gagauzia': ['Gagauzia'],
    'Transnistria (Left Bank) & Bender': ['Transnistria', 'Bender'],
}
DOM_REGIONS = {
    'Cibao Norte': ['Santiago', 'Puerto Plata', 'Espaillat'],
    'Cibao Sur': ['La Vega', 'Monseñor Nouel', 'Sánchez Ramírez'],
    'Cibao Nordeste': ['Duarte', 'María Trinidad Sánchez', 'Samaná', 'Hermanas'],
    'Cibao Noroeste': ['Valverde', 'Santiago Rodríguez', 'Monte Cristi', 'Dajabón'],
    'Valdesia': ['San Cristóbal', 'Peravia', 'San José de Ocoa', 'Azua'],
    'Enriquillo': ['Barahona', 'Bahoruco', 'Independencia', 'Pedernales'],
    'El Valle': ['San Juan', 'La Estrelleta'],
    'Yuma': ['La Romana', 'La Altagracia', 'El Seybo'],
    'Higuamo': ['San Pedro de Macorís', 'Hato Mayor', 'Monte Plata'],
    'Ozama': ['Distrito Nacional', 'Santo Domingo'],
}

_IDN_ALIAS = {'Jakarta Special Capital Region': 'Dki Jakarta', 'Special Region of Yogyakarta': 'Daerah Istimewa Yogyakarta',
  'West Java': 'Jawa Barat', 'Central Java': 'Jawa Tengah', 'East Java': 'Jawa Timur', 'West Kalimantan': 'Kalimantan Barat',
  'South Kalimantan': 'Kalimantan Selatan', 'Central Kalimantan': 'Kalimantan Tengah', 'East Kalimantan': 'Kalimantan Timur',
  'North Kalimantan': 'Kalimantan Utara', 'Bangka-Belitung Islands': 'Kepulauan Bangka Belitung', 'Riau Islands': 'Kepulauan Riau',
  'North Maluku': 'Maluku Utara', 'West Nusa Tenggara': 'Nusa Tenggara Barat', 'East Nusa Tenggara': 'Nusa Tenggara Timur',
  'West Papua': 'Papua Barat', 'West Sulawesi': 'Sulawesi Barat', 'South Sulawesi': 'Sulawesi Selatan', 'Central Sulawesi': 'Sulawesi Tengah',
  'Southeast Sulawesi': 'Sulawesi Tenggara', 'North Sulawesi': 'Sulawesi Utara', 'West Sumatra': 'Sumatera Barat',
  'South Sumatra': 'Sumatera Selatan', 'North Sumatra': 'Sumatera Utara'}
IDN_ISLANDS = {g: v + [_IDN_ALIAS[x] for x in v if x in _IDN_ALIAS] for g, v in IDN_ISLANDS.items()}
