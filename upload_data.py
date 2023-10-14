import uuid

import geopandas as gpd
import random
import psycopg2
import psycopg2.extras
import json

conn = psycopg2.connect(
    host="localhost",
    database="mapa",
    user="postgres",
    password="123456789",
    options="-c search_path=public")
conn.set_isolation_level(3)
cur = conn.cursor()
# mini funkcie
def osetrenie_zon(text):  # keďže v db majú rôzne označenie pre zóny, treba to akosi zúhľadniť
    try:
        text = str(text).split("- ")[1]
        return text
    except:
        pass
    if text == "Neaplikuje sa":
        return text
    if "5" in text:
        return "V. stupeň ochrany"
    elif "4" in text:
        return "IV. stupeň ochrany"
    elif "3" in text:
        return "III. stupeň ochrany"
    elif "2" in text:
        return "II. stupeň ochrany"
    if "C" in text:
        return "III. stupeň ochrany"
    if "B" in text:
        return "IV. stupeň ochrany"
    return text  # tu by som sa nikdy nemal dostať

def vratenie_zon_ako_cislo(text,text2):  # Do db sa teraz dava zona ako cislo


    if text == "Neaplikuje sa":
        return None
    elif "4" in text or "4" in text2 or "IV." in text or "IV." in text2:
        return 4
    elif "5" in text or "5" in text2 or "V." in text or "V." in text2:
        return 5
    elif "3" in text or "3" in text2 or "III." in text or "III." in text2:
        return 3
    elif "2" in text or "2" in text2 or "II." in text or "II." in text2:
        return 2
    if "C" in text or "C" in text2:
        return 3
    if "B" in text or "B" in text2:
        return 4
    return None  # tu by som sa nikdy nemal dostať

def pridaj_do_databazy(INSERT_STATEMENT,premenne):
    cur.execute(INSERT_STATEMENT, premenne)
    vysledok = cur.fetchone()[0]
    cur.execute("COMMIT")
    return vysledok


def pridaj_skupinu(meno,spravca,viditelnost):
    INSERT_STATEMENT = 'INSERT INTO skupiny (meno,viditelnost,spravca) VALUES (%s, %s, %s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (meno, viditelnost, spravca))

def pridaj_podskupinu(meno,spravca,skupina = None):
    INSERT_STATEMENT = 'INSERT INTO podskupiny (meno,viditelnost,spravca,skupina) VALUES (%s, %s, %s,%s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT,(meno, vytvor_viditelnost(), spravca, skupina))

def pridaj_objekt(meno, style,html,diskusia,podskupina,geometry,stupen_ochrany):
    INSERT_STATEMENT = 'INSERT INTO objekty (meno, style,html,diskusia,podskupina,geometry,stupen_ochrany) VALUES (%s, %s,%s, %s, %s,ST_SetSRID(ST_GeomFromText(%s), 4326),%s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (meno, style,html,diskusia,podskupina,geometry,stupen_ochrany))

def vytvor_viditelnost():
    INSERT_STATEMENT = 'INSERT INTO map_viditelnost_mapa (id,globalne) VALUES (%s,%s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (uuid.uuid4().__str__(),"r"))

def stupne_ochrany():
    skupina = pridaj_skupinu("Chránené oblasti",None,["*"])
    podskupiny = dict()
    shapefile = gpd.read_file("data/stupne_ochrany_v_mchu_20221006.shp")
    shapefile = shapefile.to_crs(epsg=4326)
    vysledok = dict()
    for tuples in shapefile.itertuples():
        if podskupiny.get(osetrenie_zon(tuples[1])) is None:
            podskupiny[osetrenie_zon(tuples[1])] = pridaj_podskupinu(osetrenie_zon(tuples[1]),["*"],None,skupina)
    for tuples in shapefile.itertuples():
        vysledok[osetrenie_zon(tuples[1])] = []
        for polygon in tuples[2].geoms:
            vysledok[osetrenie_zon(tuples[1])].append(polygon)
            color = ""
            fillcolor = ""
            if("V." in tuples[1]):
                color = fillcolor = "black"
            elif("IV." in tuples[1]):
                color = fillcolor = "#82152D"
            elif("III." in tuples[1]):
                color = fillcolor = "red"
            else:
                color = fillcolor = "orange"
            html = f"""
                <b>{osetrenie_zon(tuples[1])}</b><br> 
                    <a href="https://www.slovensko.sk/sk/agendy/agenda/_uzemna-ochrana-prirody-a-kraji" target="_blank" rel="noopener noreferrer">Pravidlá v tejto oblasti</a>
                    <br> 
                """
            pridaj_objekt(osetrenie_zon(tuples[1]),color,fillcolor,html,1,podskupiny[osetrenie_zon(tuples[1])],str(polygon))
    return vysledok
#!!!!!!!!!!!!!!!!!!!!!!!!!!!
#Aktualne jedine používané
def chranene_oblasti():
    shapefile = gpd.read_file("data/tk002_mchu_20221006.shp")
    shapefile['geometry'] = shapefile['geometry'].simplify(10)
    shapefile = shapefile.to_crs(epsg=4326)
    vysledok = []
    podskupiny = dict()
    pamiatky = pridaj_skupinu("Pamiatky",None,vytvor_viditelnost())
    rezervacie = pridaj_skupinu("Rezervácie", None, vytvor_viditelnost())
    ine = pridaj_skupinu("Iné chránené oblasti", None, vytvor_viditelnost())
    for tuples in shapefile.itertuples():
        if podskupiny.get(tuples[6]) is None:
            if("pamiat" in tuples[6]):
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6],None,pamiatky)
            elif("rezerv" in tuples[6]):
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6],None,rezervacie)
            else:
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6], None, ine)
    for tuples in shapefile.itertuples():
        color = ""
        fillcolor = ""
        if (tuples[6] == 'Národná prírodná rezervácia'):
            color = fillcolor = 'royalblue'

        elif (tuples[6] == 'Národná prírodná pamiatka'):
            color = fillcolor = 'indigo'

        elif (tuples[6] == 'Súkromná prírodná rezervácia'):
            color = fillcolor = "cornflowerblue"
        elif (tuples[6] == 'Prírodná pamiatka'):
            color = fillcolor = "saddlebrown"

        elif (tuples[6] == 'Prírodná rezervácia'):
            color = fillcolor = "saddlebrown" 'deepskyblue',

        elif (tuples[6] == 'Chránený krajinný prvok'):
            color = fillcolor = 'greenyellow'

        elif (tuples[6] == 'Ochranné pásmo prírodnej rezervácie'):
            color = fillcolor = 'yellowgreen'

        elif (tuples[6] == 'Ochranné pásmo národnej prírodnej rezervácie'):
            color = fillcolor = 'olive'

        elif (tuples[6] == 'Ochranné pásmo prírodnej pamiatky'):
            color = fillcolor = 'chocolate'

        elif (tuples[6] == 'Ochranné pásmo národnej prírodnej pamiatky'):
            color = fillcolor = "burlywood"

        elif (tuples[6] == 'Chránený areál'):
            color = fillcolor = 'mediumseagreen'

        elif (tuples[6] == 'Ochranné pásmo chráneného areálu'):
            color = fillcolor = 'g'
        html = f"""
            <b>{tuples[5]}</b><br> 
            {osetrenie_zon(tuples[4])}<br> 
                <a href="https://www.slovensko.sk/sk/agendy/agenda/_narodne-parky-a-prirodne-rezer/" target="_blank" rel="noopener noreferrer">Pravidlá v tejto oblasti</a>
                <br> 
            """
        style = {}
        style['fillColor'] = fillcolor
        style['color'] = color
        style = json.dumps(style)
        if ("MULTIPOLYGON" in str(tuples[13])):
            for polygon in tuples[13].geoms:
                pridaj_objekt(tuples[5], style, html, 1, podskupiny[tuples[6]],
                              str(polygon),vratenie_zon_ako_cislo(tuples[5],tuples[4]))
        else:
            pridaj_objekt(tuples[5], style, html, 1, podskupiny[tuples[6]],
                          str(tuples[13]),vratenie_zon_ako_cislo(tuples[5],tuples[4]))
    return True

def uzemia_europskeho_vyznamu():
    shapefile = gpd.read_file("data/UEV_20220831.shp")
    shapefile = shapefile.to_crs(epsg=4326)
    vysledok = []
    skupina = pridaj_skupinu("Územia európskeho významu",None,["*"])
    podskupina = pridaj_podskupinu("Územia európskeho významu",["*"],None,skupina)
    for tuples in shapefile.itertuples():
        fillcolor = color = '#003399'
        html = f"""
               <b>{tuples[2]}</b><br> 
                   <a href="https://www.slovensko.sk/sk/agendy/agenda/_narodne-parky-a-prirodne-rezer/" target="_blank" rel="noopener noreferrer">Pravidlá v tejto oblasti</a>
                   <br> 
               """
        if ("MULTIPOLYGON" in str(tuples[5])):
            for polygon in tuples[5].geoms:
                pridaj_objekt(tuples[2],color,fillcolor,html,1,podskupina,str(polygon))
        else:
            pridaj_objekt(tuples[2],color,fillcolor,html,1,podskupina,str(tuples[5]))

    return vysledok
if __name__ == '__main__':
    pass
    #stupne_ochrany()
    chranene_oblasti()
    #uzemia_europskeho_vyznamu()
