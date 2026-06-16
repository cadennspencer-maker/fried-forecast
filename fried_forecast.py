"""
The Fried Forecast 🤙
Automated surf report for Northern Spain, Portugal, France & Morocco
Scrapes surf-forecast.com and emails a formatted report every 2 weeks
"""

import os
import re
import time
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

# ─── CONFIG ───────────────────────────────────────────────────────────────────

EMAIL_SENDER    = "friedforecast@gmail.com"   # Sends from this account
EMAIL_RECIPIENT = "cadennspencer@gmail.com"   # Report delivered to this inbox
EMAIL_PASSWORD  = os.environ.get("GMAIL_APP_PASSWORD", "")  # Set in GitHub Secrets

SF_EMAIL    = os.environ.get("SF_EMAIL", "")      # Your surf-forecast.com login
SF_PASSWORD = os.environ.get("SF_PASSWORD", "")   # Set in GitHub Secrets

TOP_SPOTS_PER_REGION = 7
DELAY_BETWEEN_REQUESTS = 3  # seconds — be polite to the server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ─── SURF SPOTS ───────────────────────────────────────────────────────────────

REGIONS = {
    "🇫🇷 La Côte Basque, France": [
        ("Anglet - Chambre d'Amour",    "Anglet-Chambre-d-Amour",       "beach"),
        ("Anglet - Corsaires",           "Anglet-Corsaires",              "beach"),
        ("Anglet - L'Ocean",             "Anglet-L-Ocean",                "beach/jetty"),
        ("Anglet - La Barre",            "Anglet-La-Barre",               "river/jetty"),
        ("Anglet - La Madrague",         "Anglet-Madrague",               "beach/jetty"),
        ("Anglet - La Petite Barre",     "La-Barre",                      "beach/jetty"),
        ("Anglet - La Petite Madrague",  "Anglet-Petite-Madrague",        "beach/jetty"),
        ("Anglet - La Piscine",          "Anglet-La-Piscine",             "beach"),
        ("Anglet - Le Club",             "Anglet-Le-Club",                "beach/jetty"),
        ("Anglet - Le Furoncle",         "Le-Furoncle-La-Barre",          "breakwater"),
        ("Anglet - Les Cavaliers",       "Anglet-Les-Cavaliers",          "sandbar"),
        ("Anglet - Les Dunes",           "Anglet-Les-Dunes",              "beach"),
        ("Anglet - Les Sables d'Or",     "Anglet-Les-Sables-d-Or",        "beach"),
        ("Anglet - Marinella",           "Anglet-Marinella",              "beach"),
        ("Anglet - VVF",                 "V-V-F",                         "beach"),
        ("Belharra",                     "Belharra",                      "reef"),
        ("Biarritz - Cote des Basques",  "Cotedes-Basques",               "beach/reef"),
        ("Biarritz - Grande Plage",      "Grande-Plage",                  "beach"),
        ("Bidart",                       "Bidart",                        "beach"),
        ("Erromardie",                   "Erromardie",                    "point"),
        ("Guethary - Cenitz",            "Cenitz",                        "reef"),
        ("Guethary - Les Alcyons",       "Les-Alcyons-Avalanche",         "reef"),
        ("Guethary - Parlementia",       "Parlementia",                   "reef"),
        ("Hendaye Plage",                "Hendaye-Plage",                 "beach/reef"),
        ("Ilbarritz",                    "I-Ibarritz",                    "beach/reef"),
        ("Ilbaritz - Bora Bora",         "Ilbaritz-Bora-Bora",            "reef"),
        ("Ilbaritz - Edouard VII",       "Ilbaritz-Edouard-V-I-I",        "reef"),
        ("Ilbaritz - Marbella",          "Ilbaritz-Marbella",             "reef"),
        ("Lafitenia",                    "Lafitenia",                     "reef/point"),
        ("Le Port",                      "Le-Port-1",                     "reef"),
        ("Plage de Mayarco",             "Plage-de-Mayarco",              "reef"),
        ("St Jean de Luz - Ciboure",     "Ciboure",                       "beach/jetty"),
        ("St Jean de Luz - La Bougie",   "La-Bougie",                     "reef"),
        ("St Jean de Luz - Sainte Barbe","Sainte-Barbe-Biarritz",         "reef/jetty"),
        ("St Jean de Luz - Socoa",       "Socoa",                         "beach/jetty"),
        ("Vanthrax",                     "Vanthrax",                      "reef"),
    ],
    "🇪🇸 Pais Vasco, España": [
        ("Bakio",                        "Bakio",                         "beach"),
        ("Barinatxe - La Salvaje",       "La-Salvaje",                    "beach/reef"),
        ("Deba",                         "Deba",                          "beach/reef"),
        ("Guibeleco",                    "Guibeleco",                     "point"),
        ("Hondarribia",                  "Hondarribia",                   "beach/jetty"),
        ("Isla de Izaro",                "Islade-Izaro",                  "reef"),
        ("Karramarro",                   "Karramarro",                    "point"),
        ("La Arena",                     "La-Arena-1",                    "beach"),
        ("La Concha",                    "La-Concha",                     "reef"),
        ("Menakoz",                      "Menakoz",                       "reef"),
        ("Mundaka",                      "Mundaka",                       "river"),
        ("Mutriku",                      "Mutriku",                       "reef"),
        ("Orio",                         "Orio",                          "beach/jetty/river"),
        ("Orrua",                        "Orrua",                         "reef"),
        ("Pena Roja",                    "Pena-Roja",                     "beach"),
        ("Playa de Aizkorri",            "Playade-Aizkorri",              "point"),
        ("Playa de Arrietara",           "Playade-Arrietara",             "beach"),
        ("Playa de Arrigunaga",          "Playade-Arrigunaga",            "sandbar"),
        ("Playa de Barrika",             "Playade-Barrika",               "reef"),
        ("Playa de Ereaga",              "Playade-Ereaga",                "beach"),
        ("Playa de Gaztetape",           "Playade-Gaztetape",             "beach"),
        ("Playa de Gros",                "Playade-Gros",                  "beach"),
        ("Playa de Karraspio",           "Playade-Karraspio",             "beach"),
        ("Playa de Laga",                "Playade-Laga",                  "beach"),
        ("Playa de Laida",               "Playade-Laida",                 "river"),
        ("Playa de Ogeia",               "Playade-Ogeia",                 "reef"),
        ("Playa de Ondarreta - Pikua",   "Playade-Ondarreta_Pikua",       "point"),
        ("Playa de Ondarreta (Tennis)",  "Playade-Ondarreta_Picodel-Tenis","beach"),
        ("Plentzia",                     "Plentzia",                      "beach"),
        ("Punta Galea",                  "Punta-Galea",                   "point/jetty"),
        ("Roca Puta",                    "Roca-Puta",                     "reef"),
        ("Sopelana",                     "Sopelana",                      "beach"),
        ("Zarautz",                      "Zarautz",                       "beach"),
        ("Zumaya",                       "Zumaya",                        "beach/jetty"),
        ("Zurriola hondartza",           "Zurriola-hondartza",            "beach"),
    ],
    "🇪🇸 Cantabria, España": [
        ("Ajo",                          "Ajo",                           "beach"),
        ("Copacabana",                   "Copacabana",                    "beach"),
        ("El Arenal",                    "El-Arenal_1",                   "sandbar"),
        ("El Brusco",                    "El-Brusco",                     "beach"),
        ("El Huerto",                    "El-Huerto",                     "point"),
        ("El Sardinero - Primera",       "Playade-Sardinero",             "beach"),
        ("El Sardinero - Segunda",       "El-Sardinero",                  "beach/rocks"),
        ("Islares",                      "Islares",                       "beach"),
        ("Laredo",                       "Laredo",                        "beach"),
        ("Liencres",                     "Liencres",                      "beach"),
        ("Los Locos",                    "Los-Locos",                     "beach"),
        ("Noja",                         "Noja",                          "beach"),
        ("Playa de Arenillas (river)",   "Playade-Arenillas",             "river"),
        ("Playa de Arenillas (beach)",   "Playade-Arenillas_1",           "beach"),
        ("Playa de Berria",              "Playade-Berria",                "beach"),
        ("Playa de Brazomar",            "Playade-Brazomar",              "beach"),
        ("Playa de Galizano",            "Playade-Galizano",              "beach/reef/point"),
        ("Playa de Gerra",               "Playade-Gerra",                 "beach"),
        ("Playa de la Concha",           "Playadela-Concha",              "river"),
        ("Playa de Langre",              "Playade-Langre",                "sandbar"),
        ("Playa de los Barcos",          "Playadelos-Barcos",             "beach"),
        ("Playa de Meron",               "Playade-Meron",                 "beach"),
        ("Playa de Miono",               "Playade-Miono",                 "beach"),
        ("Playa de Orinon",              "Playade-Orinon",                "river"),
        ("Playa de Oyambre",             "Playade-Oyambre",               "beach"),
        ("Playa de Ris",                 "Playade-Ris",                   "beach"),
        ("Playa de Robayera",            "Playade-Robayera",              "river"),
        ("Playa de Somo",                "Playade-Somo",                  "beach"),
        ("Playa de Tagle",               "Playade-Tagle",                 "beach"),
        ("San Vicente",                  "San-Vicentedela-Barquera",      "beach"),
        ("San Vicente Rivermouth",       "San-Vicente_Rivermouth",        "river"),
        ("Sopico",                       "Sopico",                        "point"),
    ],
    "🇪🇸 Asturias, España": [
        ("Cabo Lastres",                 "Cabo-Lastres",                  "point"),
        ("Cala De Meron",                "Calade-Meron",                  "beach"),
        ("Concha de Artedo",             "Playa-Conchade-Artedo",         "beach"),
        ("El Mongol",                    "El-Mongol",                     "reef"),
        ("La Arena",                     "La-Arena",                      "beach"),
        ("La Nora",                      "La-Nora",                       "beach/point"),
        ("La Paloma",                    "La-Paloma_1",                   "beach"),
        ("Playa Aguilera",               "Playa-Aguilera",                "beach/point"),
        ("Playa Bahinas",                "Playa-Bahinas",                 "beach"),
        ("Playa de Andrin",              "Playade-Andrin",                "beach"),
        ("Playa de Arnao",               "Playade-Arnao",                 "beach"),
        ("Playa de Barayo",              "Playade-Barrayo",               "beach"),
        ("Playa de Bayas",               "Playade-Bayas",                 "beach"),
        ("Playa de Cadavedo",            "Playade-Cadavedo",              "reef"),
        ("Playa de Candas",              "Playade-Candas",                "beach"),
        ("Playa de Cervigon",            "Playade-Cervigon",              "reef"),
        ("Playa de Cueva",               "Playade-Cueva",                 "river"),
        ("Playa de Espana",              "Playade-Espana",                "beach/reef"),
        ("Playa de Frexulfe",            "Playade-Frexulfe",              "beach"),
        ("Playa de la Atalaya",          "Playadela-Atalayay-Cazanera",   "beach/reef"),
        ("Playa de la Cagonera",         "Playadela-Cagonera",            "beach"),
        ("Playa de la Griega",           "Playadela-Griega",              "beach"),
        ("Playa de Lastres",             "Playade-Lastres",               "river"),
        ("Playa de Llumeres",            "Playade-Llumeres",              "reef"),
        ("Playa de Luanco",              "Playade-Luanco",                "reef"),
        ("Playa de Mendia",              "Playade-Mendia",                "beach"),
        ("Playa de Navia",               "Playade-Navia",                 "beach/point"),
        ("Playa de Niembro",             "Playade-Niembro",               "beach"),
        ("Playa de Oleiros",             "Playade-Oleiros",               "reef"),
        ("Playa de Otur",                "Playade-Otur",                  "beach"),
        ("Playa de Palombina",           "Playade-Palombina",             "beach"),
        ("Playa de Penarronda",          "Playade-Penarronda",            "breakwater"),
        ("Playa de Penarrubia",          "Playade-Penarrubia",            "beach/reef"),
        ("Playa de Salinas",             "Playade-Salinas",               "beach"),
        ("Playa de San Antolin",         "Playade-San-Antolin",           "beach"),
        ("Playa de San Juan",            "Playade-San-Juan-and-Espartal", "beach/jetty"),
        ("Playa de San Lorenzo",         "Playade-San-Lorenzo",           "beach"),
        ("Playa de San Martin",          "Playade-San-Martin",            "beach"),
        ("Playa de San Pedro",           "Playade-San-Pedro",             "reef"),
        ("Playa de Santa Marina",        "Playade-Santa-Marina_Ribadesalla","beach/point/river"),
        ("Playa de Tapia",               "Playade-Tapia",                 "beach"),
        ("Playa de Torimbia",            "Playade-Torimbia",              "beach"),
        ("Playa de Tranqueru",           "Playade-Tranqueru",             "beach"),
        ("Playa de Vega",                "Playade-Vega_1",                "beach"),
        ("Playa de Vidiago",             "Playade-Vidiago",               "beach/reef"),
        ("Playa de Viso",                "Playade-Viso",                  "beach"),
        ("Playa de Xago",                "Playade-Xago",                  "beach"),
        ("Playa del Moro",               "Playadeel-Moro",                "point"),
        ("Playa los Frailes",            "Playalos-Frailes",              "beach"),
        ("Playa Santa Maria del Mar",    "Playa-Santa-Mariadel-Mar",      "beach"),
        ("Playa Tenrero",                "Playa-Tenrero",                 "beach"),
        ("Puerto de Vega",               "Puertode-Vega",                 "beach"),
        ("Rodiles",                      "Rodiles",                       "river"),
        ("Rodiles - Main Beach",         "Rodiles_Main-Beach",            "beach"),
        ("Salinas",                      "Salinas",                       "beach"),
        ("Tapia de Casariego",           "Tapiade-Casariego",             "beach/reef"),
        ("Xivares",                      "Xivares",                       "beach"),
    ],
    "🇪🇸 Galicia, España": [
        ("Louro (Playa Area Maior)",     "Playade-Louro",                 "beach"),
        ("Matadeiro",                    "Playade-Riazor",                "beach/reef"),
        ("Nemina",                       "Nemina",                        "river"),
        ("Pantin",                       "Pantin",                        "beach"),
        ("Pedra do Sal",                 "Pedra-do-Sal",                  "beach"),
        ("Playa Aguieira",               "Playa-Aguieira",                "reef"),
        ("Playa da A Marosa",            "Playa-A-Marosa",                "beach"),
        ("Playa de Area",                "Playade-Area",                  "beach"),
        ("Playa de Baldayo",             "Playade-Baldanio",              "beach"),
        ("Playa de Baleo",               "Playade-Baleo",                 "sandbar"),
        ("Playa de Barona",              "Playade-Barona",                "beach/reef"),
        ("Playa de Barra",               "Playade-Barra",                 "beach"),
        ("Playa de Barranan",            "Playade-Barranan",              "beach"),
        ("Playa de Bastiagueiro",        "Playade-Bastiagueiros",         "point"),
        ("Playa de Caion",               "Playade-Caion",                 "beach"),
        ("Playa de Campelo",             "Playade-Campelo",               "beach"),
        ("Playa de Carino",              "Playade-Carino",                "beach"),
        ("Playa de Carnota",             "Playade-Carnota",               "beach"),
        ("Playa de Castro",              "Playade-Castro",                "beach"),
        ("Playa de Doninos",             "Playade-Doninos",               "beach"),
        ("Playa de Espasante",           "Playade-Espasante",             "beach"),
        ("Playa de Esteiro",             "Playade-Esteiro",               "beach"),
        ("Playa de Fonforron",           "Playade-Fonforron",             "beach/reef"),
        ("Playa de Ladeira",             "Playade-Ladeira",               "beach"),
        ("Playa de Lanzada",             "Playade-Lanzada",               "beach/reef"),
        ("Playa de Larino",              "Playade-Larino",                "beach"),
        ("Playa de Madorra",             "Playade-Madorra",               "beach"),
        ("Playa de Malpica",             "Playade-Malpica",               "beach"),
        ("Playa de Melide",              "Playade-Melide",                "beach"),
        ("Playa de Montalbo",            "Playade-Montalbo",              "beach/reef"),
        ("Playa de Nerga",               "Playade-Negra",                 "beach"),
        ("Playa de Patos",               "Playade-Patos",                 "beach/reef"),
        ("Playa de Razo",                "Playade-Razo",                  "beach"),
        ("Playa de Rio Sieira",          "Playade-Rio-Sieira",            "beach"),
        ("Playa de Sabon",               "Playade-Sabon",                 "beach"),
        ("Playa de San Cibrao",          "Playade-San-Cibrao",            "beach"),
        ("Playa de San Miguel de Reinante","Playade-San-Miguelde-Reinante","beach"),
        ("Playa de San Roman",           "Playade-San-Roman",             "beach"),
        ("Playa de San Xurxo",           "Playade-San-Xurxo",             "beach/point"),
        ("Playa de Sarrigal",            "Playade-Sarrigal",              "beach"),
        ("Playa de Seaia",               "Playade-Seaia",                 "beach"),
        ("Playa de Soesto",              "Playa-de-Soesto",               "beach"),
        ("Playa de Traba",               "Playade-Traba",                 "beach"),
        ("Playa do Carreiro",            "Playado-Carreiro",              "river"),
        ("Playa do Orzan",               "Playade-Orzan",                 "beach"),
        ("Playa do Rostro",              "Playado-Rostro",                "beach"),
        ("Playa Rapadoira",              "Playa-Rapadoira",               "river"),
        ("Ponzos",                       "Ponzos",                        "beach"),
        ("Ria Foz",                      "Ria-Foz",                       "river"),
        ("Santa Comba",                  "Sta-Comba",                     "beach"),
        ("Santa Maria de Oia",           "Santa-Mariade-Oia",             "reef"),
        ("Serans",                       "Serans",                        "beach/reef"),
        ("Valdovino",                    "Valdovino",                     "beach"),
        ("Villarrube",                   "Villarrube",                    "beach"),
    ],
    "🇵🇹 Lisboa, Portugal": [
        ("Adraga",                       "Adraga",                        "beach/reef"),
        ("Azarujinha",                   "Azarujinha",                    "reef"),
        ("Bafureira",                    "Bafureira",                     "reef"),
        ("Bica",                         "Bica",                          "reef/point"),
        ("Bicas",                        "Bicas_1",                       "reef"),
        ("Bolina",                       "Bolina",                        "reef/point"),
        ("Carcavelos",                   "Carcavelos",                    "beach"),
        ("Caxias",                       "Caxias",                        "point"),
        ("Costa da Caparica",            "Costada-Caparica",              "beach/jetty"),
        ("Cresmina",                     "Cresmina",                      "beach"),
        ("Fonte da Telha",               "Fonte-da-Telha",                "beach"),
        ("Lagoa de Albufeira",           "Lagoa-de-Albufeira",            "beach"),
        ("Monte Estoril",                "Monte-Estoril",                 "reef/jetty"),
        ("Paco D'arcos",                 "Paco-D-arcos",                  "point"),
        ("Parede",                       "Parede",                        "point"),
        ("Poca",                         "Poca",                          "reef"),
        ("Praia da Foz Cabo Espichel",   "Praia-da-Foz-Cabo-Espichel-Sesimbra","reef"),
        ("Praia da Rainha",              "Praiada-Rainha",                "beach"),
        ("Praia da Saude",               "Praia-da-Saude",                "beach"),
        ("Praia das Macas",              "Praiadas-Macas",                "beach"),
        ("Praia do Castello",            "Praiado-Castello",              "beach"),
        ("Praia do Guincho",             "Praiado-Guincho",               "beach"),
        ("Praia do Magoito",             "Praia-do-Magoito",              "reef"),
        ("Praia do Meco",                "Praia-do-Meco",                 "beach"),
        ("Praia do Tamariz",             "Praiado-Tamariz",               "reef/jetty"),
        ("Praia Grande",                 "Praia-Grande",                  "beach"),
        ("Praia Pequena",                "Praia-Pequena",                 "beach"),
        ("Santo Amaro",                  "Santo-Amaro",                   "point"),
        ("Sao Joao",                     "Sao-Joao",                      "beach/jetty"),
        ("Sao Pedro",                    "Sao-Pedro-1",                   "point"),
        ("Torre",                        "Torre",                         "beach"),
    ],
    "🇵🇹 Ericeira, Portugal": [
        ("Backdoor",                     "Backdoor",                      "reef"),
        ("Cave",                         "Cave",                          "reef"),
        ("Coxos",                        "Coxos",                         "reef"),
        ("Crazy Left",                   "Crazy-Left",                    "reef"),
        ("Foz do Lizandro",              "Fozdo-Lizandro",                "river"),
        ("Furnas",                       "Furnas",                        "reef"),
        ("Limipicos",                    "Limipicos",                     "reef"),
        ("Malhadinha",                   "Malhadinha",                    "reef"),
        ("Pedra Branca",                 "Pedra-Branca",                  "reef"),
        ("Pontinha",                     "Pontinha",                      "reef"),
        ("Praia do Norte",               "Praiado-Norte",                 "beach/reef"),
        ("Praia do Peixe",               "Praiado-Peixe",                 "beach"),
        ("Praia do Sul",                 "Praia-do-Sul-1",                "beach/reef"),
        ("Reef",                         "Reef",                          "reef"),
        ("Ribeira D'ilhas",              "Ribeira-Dilhas",                "reef"),
        ("Sao Juliao",                   "Sao-Juliao",                    "beach"),
        ("Sao Lourenco",                 "Sao-Lourenco",                  "reef"),
        ("The Reef",                     "The-Reef",                      "reef"),
    ],
    "🇵🇹 Peniche, Portugal": [
        ("Almagreira",                   "Almagreira",                    "beach"),
        ("Baia",                         "Baia",                          "reef"),
        ("Baleal Reef",                  "Baleal-Reef",                   "beach"),
        ("Baleal Sul",                   "Baleal-Sul",                    "beach"),
        ("Belgas",                       "Belgas",                        "beach"),
        ("Cantinho",                     "Cantinho",                      "point"),
        ("Consolacao Lefts",             "Consolacao-Lefts",              "reef"),
        ("Consolacao Rights",            "Consolacao-Rights",             "point"),
        ("Ferrel",                       "Ferrel",                        "beach"),
        ("Foz do Arelho",                "Fozdo-Arelho",                  "beach"),
        ("Lagide",                       "Lagide",                        "beach/reef"),
        ("Mini Pipe",                    "Mini-Pipe",                     "reef"),
        ("Molho Leste",                  "Molhe-Leste",                   "sandbar"),
        ("Porto Batel",                  "Porto-Batel",                   "point"),
        ("Praia Azul",                   "Praia-Azul_1",                  "beach"),
        ("Praia da Areia Branca",        "Praiada-Areia-Branca",          "river"),
        ("Praia do Baleal",              "Praiado-Baleal",                "beach"),
        ("Praia do Cerro",               "Praia-do-Cerro",                "beach"),
        ("Santa Cruz",                   "Santa-Cruz",                    "beach"),
        ("Supertubos",                   "Supertubos",                    "beach/reef"),
    ],
    "🇵🇹 Algarve, Portugal": [
        ("Albufeira",                    "Albufeira",                     "beach"),
        ("Alfagar",                      "Alfagar",                       "reef"),
        ("Alvor",                        "Alvor",                         "beach"),
        ("Amoreira",                     "Amoreira",                      "beach/point"),
        ("Arrifana",                     "Arrifana",                      "beach/reef"),
        ("Barranco da Belharucas",       "Barranco-da-Belharucas",        "sandbar"),
        ("Beliche",                      "Beliche",                       "beach/point"),
        ("Burgau",                       "Burgau",                        "beach"),
        ("Carrapateira",                 "Carrapateira",                  "river"),
        ("Carriagem",                    "Carriagem",                     "reef"),
        ("Castelejo",                    "Castelejo",                     "beach/reef"),
        ("Cordoama",                     "Cordama",                       "beach"),
        ("Figueiros",                    "Figueiros",                     "beach"),
        ("Forte Novo",                   "Forte-Novo-Quarteira",          "breakwater"),
        ("Ilha de Faro",                 "Ilha-de-Faro",                  "beach"),
        ("Ilha de Tavira",               "Ilha-de-Tavira",                "beach"),
        ("Ilha Deserta",                 "Ilha-Deserta",                  "beach"),
        ("Ilha do Farol",                "Ilha-do-Farol",                 "beach"),
        ("Ingrina",                      "Ingrina",                       "reef"),
        ("Julias",                       "Julias",                        "beach"),
        ("Lage do Pescador",             "Lage-do-Pescador",              "reef"),
        ("Luz",                          "Luz-1",                         "point"),
        ("Mareta",                       "Mareta",                        "beach"),
        ("Martinhal",                    "Martinhal",                     "beach"),
        ("Meia Praia",                   "Meia-Praia",                    "beach"),
        ("Monte Clerigo",                "Monte-Clerigo",                 "river"),
        ("Ponta Ruiva",                  "Ponta-Ruiva",                   "reef"),
        ("Praia da Falesia",             "Praia-da-Falesia",              "breakwater"),
        ("Praia da Rocha",               "Praiada-Rocha",                 "beach"),
        ("Praia de Altura",              "Praia-de-Altura",               "beach"),
        ("Praia de Faro",                "Praia-de-Faro",                 "beach"),
        ("Praia de Odeceixe",            "Praiade-Odeceixe",              "beach"),
        ("Praia do Amado",               "Praiado-Amado",                 "beach"),
        ("Praia do Bordeira",            "Praia-do-Bordeira",             "sandbar"),
        ("Praia do Cabeco",              "Praia-do-Cabeco",               "beach"),
        ("Rocha Negra",                  "Luz-Rocha-Negra",               "reef"),
        ("Salema",                       "Salema",                        "sandbar"),
        ("Tonel",                        "Tonel",                         "beach/point"),
        ("Vale do Lobo",                 "Vale-do-Lobo",                  "beach"),
        ("Vale Figueira",                "Vale-Figueira",                 "beach"),
        ("Vila Real de Santo Antonio",   "Vila-Real-de-Santo-Antonia",    "beach"),
        ("Zavial",                       "Zavial",                        "point"),
    ],
    "🇲🇦 Central Morocco": [
        ("25",                           "Le-25",                         "point"),
        ("Agadir",                       "Agadir",                        "beach"),
        ("Anchor Point",                 "La-Pointedes-Ancres",           "point"),
        ("Anza",                         "Anza",                          "sandbar"),
        ("Azemmour Plage",               "Azemmour-Plage",                "beach"),
        ("Banana Beach",                 "Banana-Beach",                  "river"),
        ("Banana Point",                 "Banana-Point",                  "point"),
        ("Boilers",                      "Boilers",                       "reef"),
        ("Bouznika Point",               "Bouznika",                      "point"),
        ("Cap Sim",                      "Cap-Sim",                       "reef"),
        ("Dar Bouazza",                  "Dar-Bouazza",                   "point"),
        ("Devil's Rock",                 "Devils-Rock",                   "sandbar"),
        ("Dracula",                      "Dracula",                       "reef"),
        ("El Jadida",                    "El-Jadida",                     "beach/jetty"),
        ("Essaouira",                    "Essaouira",                     "beach"),
        ("Hash Point",                   "Hash-Point",                    "point"),
        ("Jack Beach",                   "Jackbeach",                     "beach"),
        ("Killer Point",                 "Killer-Point",                  "point"),
        ("La Source",                    "La-Source",                     "reef"),
        ("Lalafatna",                    "Lalafatna",                     "beach"),
        ("Mystery Point",                "Mystery-Point",                 "reef"),
        ("Oualidia",                     "Oualidia",                      "beach/reef"),
        ("Panoramas",                    "Panoramas",                     "beach/reef"),
        ("Pointe d'Imessouane",          "Pointed-Imessouane",            "point"),
        ("Racelafaa",                    "Racelafaa",                     "beach/reef"),
        ("Ruins",                        "Ruins",                         "beach"),
        ("Safi Garden",                  "Safi-Garden",                   "point"),
        ("Sidi Bouzid",                  "Sidi-Bouzid-Point-and-Beach",   "beach/point"),
        ("Sidi Kaouki",                  "Sidi-Kaouki",                   "sandbar"),
        ("Tamghart",                     "Tamghart",                      "beach"),
        ("Tamri-Plage",                  "Tamri-Plage",                   "river"),
    ],
    "🇲🇦 Southern Morocco": [
        ("Boats Point",                  "Boats-Point",                   "beach"),
        ("Desert Point",                 "Desert-Point",                  "point"),
        ("Ifni",                         "Ifni",                          "point/river/jetty"),
        ("Imsouane - La Cathedrale",     "La-Cathedrale",                 "beach"),
        ("Oued Massa",                   "Oued-Massa",                    "river"),
        ("Sidi Ifni",                    "Sidi-Ifni",                     "beach/reef"),
        ("Sidi Moussa D'Aglou Plage",    "Sidi-Moussa-D-Aglou-Plage",    "reef"),
        ("Tifnit",                       "Tifnit",                        "beach"),
    ],
}

# ─── SESSION / LOGIN ───────────────────────────────────────────────────────────

def create_session():
    """Create a requests session and log into surf-forecast.com"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    if not SF_EMAIL or not SF_PASSWORD:
        log.warning("No surf-forecast.com credentials set — will scrape as guest (limited data)")
        return session

    log.info("Logging into surf-forecast.com...")
    login_page = session.get("https://www.surf-forecast.com/sign_in")
    soup = BeautifulSoup(login_page.text, "lxml")

    # Grab CSRF token
    csrf = ""
    token_tag = soup.find("input", {"name": "authenticity_token"})
    if token_tag:
        csrf = token_tag.get("value", "")

    resp = session.post(
        "https://www.surf-forecast.com/sign_in",
        data={
            "user[email]":    SF_EMAIL,
            "user[password]": SF_PASSWORD,
            "authenticity_token": csrf,
            "commit": "Log In",
        },
        allow_redirects=True,
    )

    if "sign_in" in resp.url:
        log.error("Login failed — check SF_EMAIL / SF_PASSWORD secrets")
    else:
        log.info("Login successful ✓")

    return session


# ─── SCRAPING ─────────────────────────────────────────────────────────────────

def stars_from_img(img_tag):
    """Parse star rating from image alt or src text, e.g. '7 star rating'"""
    if not img_tag:
        return 0
    alt = img_tag.get("alt", "") or img_tag.get("title", "") or img_tag.get("src", "")
    m = re.search(r"(\d+)", alt)
    return int(m.group(1)) if m else 0


def parse_forecast_page(html, spot_name):
    """
    Parse the surf-forecast.com forecast table for a single spot.
    Returns list of dicts, one per 3-hour time slot.
    """
    soup = BeautifulSoup(html, "lxml")
    results = []

    # The forecast table has rows for: date/time, stars, wave height,
    # period, swell direction, wind speed, wind direction, weather
    # Row structure varies — we target the main forecast table
    table = soup.find("table", class_=re.compile(r"forecast", re.I))
    if not table:
        # Try alternate selectors
        table = soup.find("table", id=re.compile(r"forecast", re.I))
    if not table:
        log.warning(f"No forecast table found for {spot_name}")
        return results

    rows = table.find_all("tr")
    
    # Extract date headers and time slots
    dates = []
    times = []
    stars = []
    wave_heights = []
    periods = []
    swell_dirs = []
    wind_speeds = []
    wind_dirs = []
    weather_icons = []

    for row in rows:
        row_class = " ".join(row.get("class", []))
        cells = row.find_all(["td", "th"])

        if "forecast-table-days" in row_class or "days" in row_class:
            for cell in cells:
                colspan = int(cell.get("colspan", 1))
                text = cell.get_text(strip=True)
                dates.extend([text] * colspan)

        elif "forecast-table-time" in row_class or "time" in row_class:
            for cell in cells:
                times.append(cell.get_text(strip=True))

        elif "rating" in row_class or "stars" in row_class:
            for cell in cells:
                img = cell.find("img")
                stars.append(stars_from_img(img))

        elif "wave-height" in row_class or "height" in row_class:
            for cell in cells:
                txt = cell.get_text(strip=True)
                wave_heights.append(txt)

        elif "period" in row_class:
            for cell in cells:
                periods.append(cell.get_text(strip=True))

        elif "swell-direction" in row_class or "swell_direction" in row_class:
            for cell in cells:
                img = cell.find("img")
                direction = ""
                if img:
                    direction = img.get("alt", "") or img.get("title", "")
                swell_dirs.append(direction)

        elif "wind-speed" in row_class or "wind_speed" in row_class:
            for cell in cells:
                wind_speeds.append(cell.get_text(strip=True))

        elif "wind-direction" in row_class or "wind_direction" in row_class:
            for cell in cells:
                img = cell.find("img")
                direction = ""
                if img:
                    direction = img.get("alt", "") or img.get("title", "")
                wind_dirs.append(direction)

        elif "weather" in row_class:
            for cell in cells:
                img = cell.find("img")
                w = ""
                if img:
                    w = img.get("alt", "") or img.get("title", "")
                weather_icons.append(w)

    # Zip everything into slot dicts
    n = len(stars)
    for i in range(n):
        slot = {
            "spot":        spot_name,
            "date":        dates[i]        if i < len(dates)         else "",
            "time":        times[i]        if i < len(times)         else "",
            "stars":       stars[i]        if i < len(stars)         else 0,
            "wave_height": wave_heights[i] if i < len(wave_heights)  else "",
            "period":      periods[i]      if i < len(periods)       else "",
            "swell_dir":   swell_dirs[i]   if i < len(swell_dirs)    else "",
            "wind_speed":  wind_speeds[i]  if i < len(wind_speeds)   else "",
            "wind_dir":    wind_dirs[i]    if i < len(wind_dirs)     else "",
            "weather":     weather_icons[i]if i < len(weather_icons) else "",
        }
        results.append(slot)

    return results


def parse_tide_page(html):
    """
    Parse tide times and heights from the tide page.
    Returns list of dicts: {date, type (High/Low), time, height_m}
    """
    soup = BeautifulSoup(html, "lxml")
    tides = []

    table = soup.find("table", class_=re.compile(r"tide", re.I))
    if not table:
        table = soup.find("table")
    if not table:
        return tides

    current_date = ""
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        texts = [c.get_text(strip=True) for c in cells]

        # Date row
        if len(texts) == 1 and re.search(r"\d{4}", texts[0]):
            current_date = texts[0]
            continue

        # Tide row: type, time, height
        if len(texts) >= 3:
            tide_type   = texts[0]  # "High" or "Low"
            tide_time   = texts[1]
            tide_height = texts[2]
            if tide_type.lower() in ("high", "low"):
                tides.append({
                    "date":   current_date,
                    "type":   tide_type,
                    "time":   tide_time,
                    "height": tide_height,
                })

    return tides


def fetch_spot(session, slug):
    """Fetch forecast + tide data for a single spot slug."""
    base = "https://www.surf-forecast.com/breaks"
    forecast_url = f"{base}/{slug}/forecasts/latest"
    tide_url     = f"{base}/{slug}/tides/latest"

    try:
        r1 = session.get(forecast_url, timeout=20)
        time.sleep(DELAY_BETWEEN_REQUESTS)
        r2 = session.get(tide_url, timeout=20)
        time.sleep(DELAY_BETWEEN_REQUESTS)
        return r1.text, r2.text
    except Exception as e:
        log.error(f"Error fetching {slug}: {e}")
        return "", ""


# ─── REPORT BUILDING ──────────────────────────────────────────────────────────

WEATHER_EMOJI = {
    "sunny":        "☀️",
    "clear":        "☀️",
    "partly":       "⛅",
    "cloud":        "☁️",
    "overcast":     "☁️",
    "rain":         "🌧️",
    "shower":       "🌦️",
    "storm":        "⛈️",
    "thunder":      "⛈️",
    "fog":          "🌫️",
    "mist":         "🌫️",
    "snow":         "❄️",
    "hail":         "🌨️",
}

def weather_emoji(description):
    desc = description.lower()
    for key, emoji in WEATHER_EMOJI.items():
        if key in desc:
            return f"{emoji} {description}"
    return f"🌤️ {description}" if description else "🌤️"


def stars_display(n):
    filled = "⭐" * n
    return f"{filled} ({n}/10)"


def format_tides_for_date(tides, date_str):
    """Find tide entries matching a date string and format them."""
    matching = [t for t in tides if date_str in t.get("date", "")]
    if not matching:
        return "Tide data unavailable"
    parts = []
    for t in matching:
        parts.append(f"{t['type']}: {t['height']} @ {t['time']}")
    return " / ".join(parts)


def build_report(all_region_data):
    """
    all_region_data: dict of region_name -> list of (spot_name, slots, tides)
    Returns HTML string for the email.
    """
    now = datetime.now().strftime("%B %d, %Y")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    background: #0a0a1a;
    color: #e8e8e8;
    margin: 0;
    padding: 0;
  }}
  .wrapper {{
    max-width: 700px;
    margin: 0 auto;
    padding: 20px;
  }}
  .header {{
    text-align: center;
    padding: 40px 20px 20px;
    background: linear-gradient(135deg, #0f3460, #16213e);
    border-radius: 16px;
    margin-bottom: 30px;
  }}
  .header h1 {{
    font-size: 42px;
    font-weight: 900;
    color: #f4d03f;
    letter-spacing: 2px;
    margin: 0 0 8px 0;
    text-shadow: 0 2px 10px rgba(244,208,63,0.4);
  }}
  .header .subtitle {{
    color: #90caf9;
    font-size: 14px;
    letter-spacing: 1px;
  }}
  .region-block {{
    background: #111827;
    border-radius: 12px;
    margin-bottom: 30px;
    overflow: hidden;
    border: 1px solid #1e3a5f;
  }}
  .region-title {{
    background: linear-gradient(90deg, #1565c0, #0d47a1);
    padding: 16px 20px;
    font-size: 18px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1px;
  }}
  .day-block {{
    padding: 16px 20px;
    border-bottom: 1px solid #1e293b;
  }}
  .day-block:last-child {{
    border-bottom: none;
  }}
  .day-title {{
    font-size: 15px;
    font-weight: 700;
    color: #90caf9;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1e3a5f;
  }}
  .no-waves {{
    color: #f87171;
    font-weight: 600;
    font-size: 14px;
    padding: 4px 0;
  }}
  .spot-card {{
    background: #1e293b;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
    border-left: 3px solid #f4d03f;
  }}
  .spot-name {{
    font-size: 15px;
    font-weight: 700;
    color: #f4d03f;
    margin-bottom: 4px;
  }}
  .spot-type {{
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }}
  .stars {{
    font-size: 14px;
    margin-bottom: 6px;
  }}
  .best-window {{
    font-size: 12px;
    color: #34d399;
    margin-bottom: 6px;
  }}
  .data-row {{
    font-size: 12px;
    color: #cbd5e1;
    line-height: 1.8;
  }}
  .footer {{
    text-align: center;
    padding: 20px;
    color: #475569;
    font-size: 12px;
  }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🏄 The Fried Forecast</h1>
    <div class="subtitle">YOUR 16-DAY SURF REPORT &nbsp;|&nbsp; Generated {now}</div>
  </div>
"""

    for region_name, spot_data_list in all_region_data.items():
        html += f'<div class="region-block">\n'
        html += f'<div class="region-title">{region_name}</div>\n'

        # Collect all slots across all spots, grouped by date
        from collections import defaultdict
        days = defaultdict(list)  # date_str -> list of slot dicts

        tides_by_date = {}  # date_str -> formatted tide string

        for spot_name, spot_type, slots, tides in spot_data_list:
            for slot in slots:
                date = slot["date"]
                days[date].append({**slot, "spot_name": spot_name, "spot_type": spot_type})
            # Build tide lookup for this spot (use first spot's tides per date as region proxy)
            for t in tides:
                d = t["date"]
                if d not in tides_by_date:
                    tides_by_date[d] = []
                tides_by_date[d].append(t)

        if not days:
            html += '<div class="day-block"><div class="no-waves">⚠️ Could not retrieve forecast data for this region.</div></div>\n'
        else:
            for date_str in sorted(days.keys()):
                html += f'<div class="day-block">\n'
                html += f'<div class="day-title">📅 {date_str}</div>\n'

                # Get all slots for this date, find best per spot (highest stars)
                spot_best = {}
                for slot in days[date_str]:
                    sname = slot["spot_name"]
                    if sname not in spot_best or slot["stars"] > spot_best[sname]["stars"]:
                        spot_best[sname] = slot

                # Sort by stars descending, take top 7
                ranked = sorted(spot_best.values(), key=lambda x: x["stars"], reverse=True)
                top = [s for s in ranked if s["stars"] > 0][:TOP_SPOTS_PER_REGION]

                if not top:
                    html += '<div class="no-waves">🤙 Waves Blow!</div>\n'
                else:
                    for i, slot in enumerate(top, 1):
                        # Format tide for this date
                        tide_entries = tides_by_date.get(date_str, [])
                        tide_str = "Tide data unavailable"
                        if tide_entries:
                            parts = []
                            for t in tide_entries[:4]:
                                parts.append(f"{t['type']}: {t.get('height','?')} @ {t.get('time','?')}")
                            tide_str = " / ".join(parts)

                        html += f"""
<div class="spot-card">
  <div class="spot-name">#{i} {slot['spot_name']}</div>
  <div class="spot-type">{slot['spot_type']}</div>
  <div class="stars">{stars_display(slot['stars'])}</div>
  <div class="best-window">🕐 Best window: {slot['time']}</div>
  <div class="data-row">
    🌊 {slot['wave_height']} &nbsp;|&nbsp; ⏱️ {slot['period']}s &nbsp;|&nbsp; 🧭 Swell: {slot['swell_dir']}<br>
    💨 Wind: {slot['wind_dir']} {slot['wind_speed']}<br>
    🌊 Tides: {tide_str}<br>
    {weather_emoji(slot['weather'])}
  </div>
</div>
"""
                html += '</div>\n'  # end day-block

        html += '</div>\n'  # end region-block

    html += """
  <div class="footer">
    🤙 The Fried Forecast — Stay Salty<br>
    Data sourced from surf-forecast.com
  </div>
</div>
</body>
</html>
"""
    return html


# ─── EMAIL ────────────────────────────────────────────────────────────────────

def send_email(html_body):
    if not EMAIL_PASSWORD:
        log.error("GMAIL_APP_PASSWORD not set — cannot send email")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏄 The Fried Forecast — {datetime.now().strftime('%B %d, %Y')}"
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECIPIENT

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        log.info("✅ Fried Forecast email sent successfully!")
    except Exception as e:
        log.error(f"Failed to send email: {e}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    log.info("🏄 Starting The Fried Forecast...")

    session = create_session()
    all_region_data = {}

    for region_name, spots in REGIONS.items():
        log.info(f"Scraping region: {region_name} ({len(spots)} spots)")
        spot_data_list = []

        for spot_name, slug, spot_type in spots:
            log.info(f"  → {spot_name}")
            forecast_html, tide_html = fetch_spot(session, slug)

            slots = parse_forecast_page(forecast_html, spot_name) if forecast_html else []
            tides = parse_tide_page(tide_html) if tide_html else []

            spot_data_list.append((spot_name, spot_type, slots, tides))

        all_region_data[region_name] = spot_data_list

    log.info("Building report...")
    html = build_report(all_region_data)

    log.info("Sending email...")
    send_email(html)

    log.info("Done! 🤙")


if __name__ == "__main__":
    main()
