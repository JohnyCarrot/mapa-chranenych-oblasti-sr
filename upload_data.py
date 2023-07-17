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

def pridaj_do_databazy(INSERT_STATEMENT,premenne):
    cur.execute(INSERT_STATEMENT, premenne)
    vysledok = cur.fetchone()[0]
    cur.execute("COMMIT")
    return vysledok


def pridaj_skupinu(meno,spravca,viditelnost):
    INSERT_STATEMENT = 'INSERT INTO skupiny (meno,viditelnost,spravca) VALUES (%s, %s, %s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (meno, viditelnost, spravca))

def pridaj_podskupinu(meno,viditelnost,spravca,skupina = None):
    INSERT_STATEMENT = 'INSERT INTO podskupiny (meno,viditelnost,spravca,skupina) VALUES (%s, %s, %s,%s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT,(meno, viditelnost, spravca, skupina))

def pridaj_objekt(meno, color, fillcolor,html,diskusia,podskupina,geometry):
    INSERT_STATEMENT = 'INSERT INTO objekty (meno, color, fillcolor,html,diskusia,podskupina,geometry) VALUES (%s, %s, %s,%s, %s, %s,ST_SetSRID(ST_GeomFromText(%s), 4326)) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (meno, color, fillcolor,html,diskusia,podskupina,geometry))

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

def chranene_oblasti():
    shapefile = gpd.read_file("data/tk002_mchu_20221006.shp")
    shapefile = shapefile.to_crs(epsg=4326)
    vysledok = []
    podskupiny = dict()
    pamiatky = pridaj_skupinu("Pamiatky",None,["*"])
    rezervacie = pridaj_skupinu("Rezervácie", None, ["*"])
    ine = pridaj_skupinu("Iné chránené oblasti", None, ["*"])
    for tuples in shapefile.itertuples():
        if podskupiny.get(tuples[6]) is None:
            if("pamiat" in tuples[6]):
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6],["*"],None,pamiatky)
            elif("rezerv" in tuples[6]):
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6],["*"],None,rezervacie)
            else:
                podskupiny[tuples[6]] = pridaj_podskupinu(tuples[6], ["*"], None, ine)
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

        if ("MULTIPOLYGON" in str(tuples[13])):
            for polygon in tuples[13].geoms:
                pridaj_objekt(osetrenie_zon(tuples[5]), color, fillcolor, html, 1, podskupiny[tuples[6]],
                              str(polygon))
        else:
            pridaj_objekt(osetrenie_zon(tuples[5]), color, fillcolor, html, 1, podskupiny[tuples[6]],
                          str(tuples[13]))
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
