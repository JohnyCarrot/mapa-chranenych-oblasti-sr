import traceback

import branca
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render
import folium
import time
import geocoder
import random
import json
from django.core.serializers import json as json_ser
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from folium import plugins
from django.db import connection
from draw_custom import Draw as Draw_custom
from geoman import Geoman as Geoman
from geoman_user import Geoman as Geoman_user
from geocoder_custom import Geocoder as Geocoder_custom
from easy_button_non_universal import EasyButton as EasyButton
from django.shortcuts import render, redirect
from .forms import NewUserForm, NewUserForm_valid_check
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from friendship.models import Friend, Follow, Block, FriendshipRequest, FriendshipManager
from django.http import HttpResponseRedirect, HttpResponse
from .models import Skupiny,Podskupiny,Objekty, Profile, Viditelnost_mapa, Notifikacie, Diskusia, Diskusny_prispevok
from django.contrib.gis.geos import GEOSGeometry
cur = connection.cursor()


def pridaj_do_databazy(INSERT_STATEMENT,premenne):
    cur.execute(INSERT_STATEMENT, premenne)
    vysledok = cur.fetchone()[0]
    cur.execute("COMMIT")
    return vysledok


def pridaj_skupinu(meno,spravca,viditelnost,nastavenia = None):
    INSERT_STATEMENT = 'INSERT INTO skupiny (meno,viditelnost,spravca,nastavenia) VALUES (%s, %s, %s, %s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT, (meno, viditelnost, spravca, nastavenia))

def pridaj_podskupinu(meno,viditelnost,spravca,skupina = None):
    INSERT_STATEMENT = 'INSERT INTO podskupiny (meno,viditelnost,spravca,skupina) VALUES (%s, %s, %s,%s) RETURNING id;'
    return pridaj_do_databazy(INSERT_STATEMENT,(meno, viditelnost, spravca, skupina))

def sulad_s_nastavenim_mapy(nastavenie,objekt):
    if(nastavenie == None):
        return True
    if(nastavenie.stupen2 == False and objekt.stupen_ochrany==2): return False
    if (nastavenie.stupen3 == False and objekt.stupen_ochrany == 3): return False
    if (nastavenie.stupen4 == False and objekt.stupen_ochrany == 4): return False
    if (nastavenie.stupen5 == False and objekt.stupen_ochrany == 5): return False
    return True

def navbar_zapni_administraciu(user):
    if user.is_authenticated == False: return False
    if user.is_superuser: return True
    for skupina in Skupiny.objects.filter(spravca=None).order_by('priorita'):
        permisie_skupina = False
        permisie_skupina_temp = False
        if type(skupina.viditelnost.uzivatelia)==dict and skupina.viditelnost.uzivatelia.get(user.username) != None and "w" in skupina.viditelnost.uzivatelia.get(user.username):
            permisie_skupina = True

        for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
            if type(podskupina.viditelnost.uzivatelia)==dict and podskupina.viditelnost.uzivatelia.get(user.username) != None and "w" in podskupina.viditelnost.uzivatelia.get(user.username):
                permisie_skupina_temp = True

        if permisie_skupina or permisie_skupina_temp:
            return True
    return False




def pridaj_objekty_do_podskupiny(podskupina,podskupina_v_mape,geocoder, uzivatel = None):
    if(uzivatel == None or uzivatel.is_authenticated == False):
        nastavenie_mapy = None
    else:
        profil = Profile.objects.get(user_id=uzivatel.id)
        nastavenie_mapy = profil.map_settings
    for objekt in Objekty.objects.all():
        nastavenia = None
        zdielane = False
        zdielane_w = False
        if(sulad_s_nastavenim_mapy(nastavenie_mapy,objekt)==False):
            continue
            #Započatie html
        html="""
        <!DOCTYPE html>
            <html>
            <head>
            <script src="https://unpkg.com/htmx.org@1.9.9"></script>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" integrity="sha512-z3gLpd7yknf1YoNbCzqRKc4qyor8gaKU1qmn+CShxbuBusANI9QpRohGBreCFkKxLhei6S9CQXFEbbKuqLg0DA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <!-- Bootstrap CSS / JS-->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css" integrity="sha384-xOolHFLEh07PJGoPkLv1IbcEPTNtaed2xpHsD9ESMhqIYd0nLMwNLD69Npy4HI+N" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js" integrity="sha384-DfXdz2htPH0lsSSs5nCTpuj/zy4C+OGpamoFVy38MVBnE+IbbVYUew+OrCXaRkfj" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-Fy6S3B9q64WdZWQUiU+q4/2Lc9npb8tCaSX9FK7E8HnRr0Jz8D6OP9dO5Vg3Q9ct" crossorigin="anonymous"></script>

            </head>
            <body>
            <div style="font-size: 13.5px;">
        """#Započatie html
        html += objekt.html

        if objekt.nastavenia != None:
            nastavenia = json.loads(objekt.nastavenia)
            if "deleted" in nastavenia and nastavenia['deleted'] == True:
                continue

        if(objekt.nastavenia != None and uzivatel!= None and uzivatel.is_authenticated):
            nastavenia = json.loads(objekt.nastavenia)
            if"shared_with" in nastavenia and uzivatel.username in nastavenia["shared_with"] and nastavenia["shared_with"][uzivatel.username]==podskupina.id:
                zdielane = True
                html+=f"""<p style="white-space: nowrap">Zdieľané používateľom: <br><b>{objekt.podskupina.spravca}</b></p>"""
                html += f"""<a href="#" hx-post="http://127.0.0.1:8000/htmx/?username={uzivatel.username}&request=zrusit_zdielanie&ifrejm=true&objekt={objekt.id}&zdielane_s={uzivatel.username}" hx-swap="outerHTML" style="margin:5px;">Zrušiť zdieľanie</a> <br><br>"""

                pseudo_podskupina_objektu = Podskupiny.objects.get(pk=nastavenia["shared_with"][uzivatel.username])
                viditelnost = pseudo_podskupina_objektu.viditelnost
                if "w" in viditelnost.uzivatelia[uzivatel.username]:
                    zdielane_w = True

        if(objekt.podskupina_id!=podskupina.id and zdielane == False):
            continue
        if (objekt.diskusia.aktivna): html+=f"""<a href="http://127.0.0.1:8000/diskusia?q={objekt.diskusia.id}" target="_blank" rel="noopener noreferrer">Diskusia</a>"""
        if (uzivatel != None and zdielane == False and podskupina.spravca == uzivatel.username):
            html+=f"""
                    <button hx-post="http://127.0.0.1:8000/htmx/?username={uzivatel.username}&request=zdielanie_list&objekt={objekt.id}" hx-swap="outerHTML">
                        Zdieľať
                    </button> 
                    <br>
            """
        if(uzivatel!= None and zdielane == False and podskupina.spravca == uzivatel.username) or (zdielane_w):
            html+=f"""<button onclick="uprav_uzivatelsku_vrstvu('{objekt.id}','{uzivatel.username}');"><i class="fa-solid fa-pencil"></i></button>"""
            if podskupina.spravca == uzivatel.username and zdielane == False and zdielane_w == False:
                html += f"""<button onclick="zmaz_uzivatelsku_vrstvu('{objekt.id}','{uzivatel.username}');"><i class="fa-solid fa-trash"></i></button>"""
            html+="""
                    <script>
                async function uprav_uzivatelsku_vrstvu(id,meno) {
                  let user = {
                  id: id,
                  username: meno,
                  uprav_vrstvu_iframe: null
                };

                let response = await fetch('http://127.0.0.1:8000/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });

           return true;
        }
        
            async function zmaz_uzivatelsku_vrstvu(id,meno) {
                  let user = {
                  id: id,
                  username: meno,
                  zmaz_vrstvu_iframe: null
                };

                let response = await fetch('http://127.0.0.1:8000/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });

           return true;
        }
            </script>
            """



        geometria = GEOSGeometry(objekt.geometry)
        geometria_cela = json.loads(geometria.json)
        geometria_cela['serverID'] = objekt.id
        geometria_cela['podskupina_spravca'] = objekt.podskupina.spravca# zrejme zamenit / pridať len za pravo menit
        geometria_cela['zdielane_w'] = False #Zdielane a pravo zapisovat
        if zdielane and zdielane_w:
                geometria_cela['zdielane_w'] = True
        geometria_cela['popup_HTML'] = objekt.html

        html+="</div></body></html>" #Koniec html
        iframe = branca.element.IFrame(html=html, width='150px',ratio='100%')

        if objekt.style== None:
            objekt.style={}
            objekt.save()
        styl = objekt.style
        folium.GeoJson(geometria_cela, style_function=lambda x, styl=styl: styl,name=objekt.meno).add_to(podskupina_v_mape).add_child(
            folium.Popup(iframe, max_width=500,lazy=True))
        geocoder.append({"name":objekt.meno,"center":[geometria.centroid.coord_seq.getY(0),geometria.centroid.coord_seq.getX(0)]})



def over_viditelnost(viditelnost,prihlaseny = False,username = "",permisia="r",vlastnik=""):
    if viditelnost == None: return False

    #try:
     #   if vlastnik == None and prihlaseny and User.objects.get(username=username).is_superuser:
       #     return True
    #except:
     #   pass

    if prihlaseny and viditelnost.uzivatelia is not None and username in viditelnost.uzivatelia and permisia not in viditelnost.uzivatelia[username]:
        return False

    if viditelnost.globalne is not None and permisia in viditelnost.globalne:
        if prihlaseny and username != "" and viditelnost.prihlaseny is not None and viditelnost.prihlaseny !="" and permisia not in viditelnost.prihlaseny:
            return False
        return True

    if prihlaseny and viditelnost.prihlaseny is not None and permisia in viditelnost.prihlaseny: return True

    if prihlaseny and viditelnost.uzivatelia is not None and username in viditelnost.uzivatelia and permisia in viditelnost.uzivatelia[username]:
        return True


    return False

def vrat_skupinu_vlastnych_objektov_uzivatela(username):
    cur.execute(f"SELECT id from skupiny WHERE nastavenia::jsonb ? 'own' and spravca = '{username}' limit 1;")
    k = cur.fetchone()
    if(k==None): return None
    return str(k[0])

def vrat_skupinu_s_uzivatelom_zdielanych_objektov(username):
    cur.execute(f"SELECT id from skupiny WHERE nastavenia::jsonb ? 'shared' and spravca = '{username}' limit 1;")
    k = cur.fetchone()
    if(k==None): return None
    return k[0]

def vrat_zdielane_objekty_s_uzivatelom(username):
    objekty_cele = []
    for objekt in Objekty.objects.all():
        if objekt.nastavenia != None:
            nastavenia = json.loads(objekt.nastavenia)
            if"shared_with" in nastavenia and username in nastavenia["shared_with"]:
                objekty_cele.append(objekt)
    return objekty_cele




def index(requests):
    if requests.user.is_authenticated:
        if vrat_skupinu_vlastnych_objektov_uzivatela(username=requests.user.username) == None:
            viditelnost = Viditelnost_mapa()
            viditelnost.uzivatelia[requests.user.username] = "rw"
            viditelnost.save()
            pridaj_skupinu("Vlastné objekty",requests.user.username,viditelnost.id,nastavenia = json.dumps({'own': None,}))
        if vrat_skupinu_s_uzivatelom_zdielanych_objektov(requests.user.username) == None:
            viditelnost = Viditelnost_mapa()
            viditelnost.uzivatelia[requests.user.username] = "rw"
            viditelnost.save()
            pridaj_skupinu("So mnou zdieľané objekty",requests.user.username,viditelnost.id,nastavenia = json.dumps({'shared': None,}))
    #Pridanie objektu užívateľom:
    if (requests.user.is_authenticated and requests.GET.get('new_object') != None and requests.GET.get('new_object_name')!=None):
        dictData = json.loads(requests.GET.get('new_object'))
        viditelnost = Viditelnost_mapa()
        viditelnost.uzivatelia[requests.user.username] = "rw"
        viditelnost.save()
        podskupina_noveho_objektu = Podskupiny()
        podskupina_noveho_objektu.meno = requests.GET.get('new_object_name')
        podskupina_noveho_objektu.viditelnost = viditelnost
        podskupina_noveho_objektu.spravca = requests.user.username
        podskupina_noveho_objektu.skupina = Skupiny.objects.get(id=vrat_skupinu_vlastnych_objektov_uzivatela(requests.user.username))
        podskupina_noveho_objektu.save()
        INSERT_STATEMENT = 'INSERT INTO objekty (meno, style,html,diskusia,podskupina,geometry) VALUES (%s, %s,%s, %s, %s,ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)) RETURNING id;'
        cur.execute(INSERT_STATEMENT, (requests.GET.get('new_object_name'),None,"",0,podskupina_noveho_objektu.id,str(dictData['geometry'])   )  )
        return HttpResponseRedirect(requests.path_info)

    return render(requests, 'index/index.html')

def render_mapy(requests):
    start_time = time.time()
    start_time_temp = time.time()
    #Normálne načítanie
    m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                   zoom_start=8,
                   prefer_canvas=False,
                   # crs="EPSG3857",

                   )
    geocoder_vlastne_vyhladanie = []
    skupiny_v_navigacii = dict()
    for skupina in Skupiny.objects.all().order_by('priorita'):
        if over_viditelnost(skupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username),vlastnik=skupina.spravca):
            _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
            _skupina_v_mape.add_to(m)
            podskupiny_v_mape = []
            for podskupina in Podskupiny.objects.all().order_by('priorita'):
                if(skupina.id ==podskupina.skupina_id and over_viditelnost(podskupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username),vlastnik=podskupina.spravca)):
                    _podskupina_v_mape = folium.plugins.FeatureGroupSubGroup(_skupina_v_mape, name=podskupina.meno)
                    _podskupina_v_mape.add_to(m)
                    pridaj_objekty_do_podskupiny(podskupina,_podskupina_v_mape,uzivatel=requests.user,geocoder=geocoder_vlastne_vyhladanie)
                    podskupiny_v_mape.append(_podskupina_v_mape)
            skupiny_v_navigacii[skupina.meno] = podskupiny_v_mape
    print(f"---Všetky objekty v db: %s seconds ---" % (time.time() - start_time_temp))

    start_time_temp = time.time()

    # mapa nastavenie
    folium.plugins.Fullscreen().add_to(m)
    Geocoder_custom(collapsed=True, add_marker=True, suggestions = geocoder_vlastne_vyhladanie).add_to(m)
    folium.plugins.GroupedLayerControl(skupiny_v_navigacii, exclusive_groups=False).add_to(m)
    folium.plugins.LocateControl(auto_start=False).add_to(m)
    if(requests.user.is_authenticated):
        map_setting = Profile.objects.get(user_id=requests.user.id).map_settings
        EasyButton(map_setting.stupen2,map_setting.stupen3,map_setting.stupen4,map_setting.stupen5).add_to(m)
        Geoman_user(username=requests.user.username).add_to(m)
        Draw_custom(export=False,draw_options= {"circle": False,"circlemarker": False}).add_to(m)
    print(f"---Pluginy: %s seconds ---" % (time.time() - start_time_temp))
    start_time_temp = time.time()
    #m = m._repr_html_()
    fig = branca.element.Figure(height='100%')
    fig.add_child(m)
    context = {
        'm': fig._repr_html_(),
    }

    context['navbar_administracia'] = navbar_zapni_administraciu(requests.user) #Neoverovať prihlásenie !!!
    print(f"---Generacia mapy: %s seconds ---" % (time.time() - start_time_temp))
    print(f"---celá stránka %s seconds ---" % (time.time() - start_time))
    return HttpResponse(m._repr_html_(), content_type="text/plain")

# Koniec mapy, začiatok diskusného fóra
def forum(requests):
    context = {}
    if "q" in requests.GET:
        context['diskusia'] = Diskusia.objects.get(id = requests.GET.get('q'))
    return render(requests, 'forum/diskusia.html',context)

@login_required
def profil(requests):
    if "u" in requests.GET and User.objects.filter(username=requests.GET['u']).exists():
        context = {}
        uzivatel = User.objects.get(username=requests.GET['u'])
        profil = Profile.objects.get(user=uzivatel)
        context['uzivatel'] = uzivatel
        context['profil'] = profil
        return render(requests, 'profil/profil.html',context)
    else:
        return HttpResponse("Profil neexistuje")
def subgroup_edit(requests):
    return render(requests, 'spravuj_podskupiny/index.html')

@login_required
def friends_main_page(requests):
    context = {}


    context['navbar_administracia'] = navbar_zapni_administraciu(requests.user)
    return render(requests, 'friends/friends.html',context)


def register_request(request):
    errors = {}
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            viditelnost = Viditelnost_mapa()
            viditelnost.uzivatelia[user.username] = "rw"
            viditelnost.save()
            vlastne_objekty_skupina = pridaj_skupinu("Vlastné objekty",user.username,viditelnost.id,nastavenia = json.dumps({'own': None,}))
            zdielane_objekty_podskupina = pridaj_skupinu("So mnou zdieľané objekty",user.username,viditelnost.id,nastavenia = json.dumps({'shared': None,}))
            return redirect('/')
        #messages.error(request, "Unsuccessful registration. Invalid information.")
        errors = form.errors
    form = NewUserForm()
    return render(request=request, template_name="main/register.html", context={"register_form": form,"errors": errors})

def login_request(request):
    errors = {}
    if request.method == "POST":
        form = AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if "next" in request.GET:
                return redirect(request.GET.get('next'))
            return redirect('/')
        errors = form.errors
    form = AuthenticationForm()
    return render(request=request, template_name="main/login.html", context={"register_form": form,"errors": errors})

uzivatelska_vrstva_na_zmazanie = "" #Obchádzanie text/html src iframu
uzivatelska_vrstva_na_upravu = ""
opravneny_uzivatel = ""
@csrf_exempt
def api_request(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            global uzivatelska_vrstva_na_upravu
            global uzivatelska_vrstva_na_zmazanie
            global opravneny_uzivatel
            if("stupen2" in body and "stupen3" in body and "stupen4" in body and "stupen5" in body):
                profil = Profile.objects.get(user_id=request.user.id)
                mapa_nastavenia = profil.map_settings
                mapa_nastavenia.stupen2 = body['stupen2']
                mapa_nastavenia.stupen3 = body['stupen3']
                mapa_nastavenia.stupen4 = body['stupen4']
                mapa_nastavenia.stupen5 = body['stupen5']
                mapa_nastavenia.save()
                return HttpResponse(status=202)

            if "uzivatel_nastavenia_ulozit" in body and "email" in body and "location" in body:
                profilcek = Profile.objects.get(user=request.user)
                email = body['email']
                if body['email']=="":
                    email = request.user.email
                location = body['location']
                if body['location'] == "":
                    location = profilcek.location
                dob = body['datum_narodenia']
                passwd = body['password']
                passwd2 = body['password2']
                data = {
                  "email": email,
                  "location": location,
                  "date_of_birth": dob,
                }
                form = NewUserForm_valid_check(data)
                response_data = form.errors
                response_data.pop("password1", None)
                response_data.pop("password2", None)
                if response_data == {}:
                    request.user.email = email
                    profilcek.location = location
                    if parse_date(dob) is not None:
                        profilcek.birth_date = parse_date(dob)
                    request.user.save()
                    profilcek.save()
                    if passwd!="" and passwd==passwd2:
                        request.user.set_password(passwd)
                        request.user.save()
                    return HttpResponse(status=201)
                return HttpResponse(json.dumps(response_data), content_type="application/json",status=301)

            if "diskusia_novy_prispevok" in body and "html" in body and "id_diskusie" in body:
                diskusia = Diskusia.objects.get(id = body['id_diskusie'])
                novy_prispevok = Diskusny_prispevok()
                novy_prispevok.diskusia = diskusia
                novy_prispevok.sprava = body['html']
                novy_prispevok.user = request.user
                novy_prispevok.save()
                return HttpResponse(status=201)
            if "objekt_zmazanie_navzdy" in body and "objekt_id" in body:
                Objekty.objects.get(id=body['objekt_id']).delete()
                return HttpResponse(status=201)

            if "obnov_objekt_z_kosa" in body and "objekt_id" in body:
                objekt = Objekty.objects.get(id=body['objekt_id'])
                nastavenia = json.loads(objekt.nastavenia)
                nastavenia['deleted'] = False
                objekt.nastavenia = json.dumps(nastavenia)
                objekt.save()
                return HttpResponse(status=201)

            if "uprav_vrstvu_iframe" in body and "id" in body and "username" in body:
                opravneny_uzivatel = body['username']
                uzivatelska_vrstva_na_upravu = body['id']
                return HttpResponse(status=202)
            if "zmaz_vrstvu_iframe" in body and "id" in body and "username" in body:
                opravneny_uzivatel = body['username']
                uzivatelska_vrstva_na_zmazanie = body['id']
                return HttpResponse(status=202)

            if "dostan_vrstvy_zmazanie_iframe" in body and "username" in body:
                if uzivatelska_vrstva_na_zmazanie =="" or body['username']!= opravneny_uzivatel:
                    return HttpResponse("", status=304)
                user = User.objects.get(username=body['username'])
                objekt = Objekty.objects.get(pk=uzivatelska_vrstva_na_zmazanie)
                if objekt.podskupina.spravca == user.username:
                    vysledok = str(uzivatelska_vrstva_na_zmazanie)
                    uzivatelska_vrstva_na_zmazanie = ""
                    return HttpResponse(vysledok, status=202)
                if objekt.nastavenia != None:
                    nastavenia = json.loads(objekt.nastavenia)
                    if "shared_with" in nastavenia and user.username in nastavenia["shared_with"]:
                        pseudo_podskupina_objektu = Podskupiny.objects.get(
                            pk=nastavenia["shared_with"][user.username])
                        viditelnost = pseudo_podskupina_objektu.viditelnost
                        if "w" in viditelnost.uzivatelia[user.username]:
                            vysledok = str(uzivatelska_vrstva_na_zmazanie)
                            uzivatelska_vrstva_na_zmazanie = ""
                            return HttpResponse(vysledok, status=202)

                return HttpResponse("", status=304)

            if "dostan_vrstvy_uprava_iframe" in body and "username" in body:
                if uzivatelska_vrstva_na_upravu =="" or body['username']!= opravneny_uzivatel:
                    return HttpResponse("", status=304)
                user = User.objects.get(username=body['username'])
                objekt = Objekty.objects.get(pk=uzivatelska_vrstva_na_upravu)
                if objekt.podskupina.spravca == user.username:
                    vysledok = str(uzivatelska_vrstva_na_upravu)
                    uzivatelska_vrstva_na_upravu = ""
                    return HttpResponse(vysledok, status=202)
                if objekt.nastavenia != None:
                    nastavenia = json.loads(objekt.nastavenia)
                    if "shared_with" in nastavenia and user.username in nastavenia["shared_with"]:
                        pseudo_podskupina_objektu = Podskupiny.objects.get(
                            pk=nastavenia["shared_with"][user.username])
                        viditelnost = pseudo_podskupina_objektu.viditelnost
                        if "w" in viditelnost.uzivatelia[user.username]:
                            vysledok = str(uzivatelska_vrstva_na_upravu)
                            uzivatelska_vrstva_na_upravu = ""
                            return HttpResponse(vysledok, status=202)

                return HttpResponse("", status=304)

            if "toggle_zapis_zdielania" in body and "uzivatel" in body and "id_objektu" in body:
                objekt = Objekty.objects.get(pk=body.get('id_objektu'))
                other_user = User.objects.get(pk=body.get('uzivatel'))
                nastavenia = json.loads(objekt.nastavenia)
                pseudo_podskupina_objektu = Podskupiny.objects.get(pk = nastavenia["shared_with"][other_user.username])
                viditelnost = pseudo_podskupina_objektu.viditelnost
                if "w" in viditelnost.uzivatelia[other_user.username]:
                    viditelnost.uzivatelia[other_user.username] = viditelnost.uzivatelia[other_user.username].replace('w', '')
                else:
                    viditelnost.uzivatelia[other_user.username] +="w"
                viditelnost.save()
                return HttpResponse(status=202)
            if "zrusit_zdielanie" in body and "uzivatel_meno" in body and "id_objektu" in body:
                zdielany_objekt = Objekty.objects.get(id=body.get('id_objektu'))
                priatel = User.objects.get(username=body.get('uzivatel_meno')).username  # !!!
                nastavenia = json.loads(zdielany_objekt.nastavenia)
                if "shared_with" in nastavenia and (priatel in nastavenia["shared_with"]):
                    Podskupiny.objects.get(id=nastavenia["shared_with"][priatel]).delete()
                    nastavenia["shared_with"].pop(priatel)
                    zdielany_objekt.nastavenia = json.dumps(nastavenia)
                    zdielany_objekt.save()

                return HttpResponse(status=202)
            ##########Administrácia##########
            if "podskupina" in body and "id" in body and "priorita" in body:
                podskupina = Podskupiny.objects.get(id=body['id'])
                podskupina.priorita = body['priorita']
                podskupina.save()
                return HttpResponse(status=202)
            if "skupina" in body and "id" in body and "priorita" in body:
                skupina = Skupiny.objects.get(id=body['id'])
                skupina.priorita = body['priorita']
                skupina.save()
                return HttpResponse(status=202)
            if "daj_mapu" in body and "id" in body and "skupina" in body:
                m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                               zoom_start=8,
                               width=1280, height=720,
                               prefer_canvas=False,
                               # crs="EPSG3857",

                               )
                podskupiny_id_pre_pridavanie_objektu = []
                if body["skupina"]:
                    geocoder_vlastne_vyhladanie = []
                    skupina_v_navigacii = dict()
                    skupina = Skupiny.objects.get(id=body['id'])
                    _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
                    _skupina_v_mape.add_to(m)
                    podskupiny_v_mape = []
                    for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
                        _podskupina_v_mape = folium.plugins.FeatureGroupSubGroup(_skupina_v_mape, name=podskupina.meno)
                        _podskupina_v_mape.add_to(m)
                        pridaj_objekty_do_podskupiny(podskupina, _podskupina_v_mape, uzivatel=request.user,
                                                     geocoder=geocoder_vlastne_vyhladanie)
                        podskupiny_v_mape.append(_podskupina_v_mape)
                        podskupiny_id_pre_pridavanie_objektu.append(podskupina)
                    skupina_v_navigacii[skupina.meno] = podskupiny_v_mape
                else:
                    podskupina = Podskupiny.objects.get(id=body['id'])
                    podskupiny_id_pre_pridavanie_objektu.append(podskupina)
                    geocoder_vlastne_vyhladanie = []
                    skupina_v_navigacii = dict()
                    skupina = podskupina.skupina
                    _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
                    _skupina_v_mape.add_to(m)
                    podskupiny_v_mape = []
                    _podskupina_v_mape = folium.plugins.FeatureGroupSubGroup(_skupina_v_mape, name=podskupina.meno)
                    _podskupina_v_mape.add_to(m)
                    pridaj_objekty_do_podskupiny(podskupina, _podskupina_v_mape, uzivatel=request.user,
                                                 geocoder=geocoder_vlastne_vyhladanie)
                    podskupiny_v_mape.append(_podskupina_v_mape)
                    skupina_v_navigacii[skupina.meno] = podskupiny_v_mape
                folium.plugins.Fullscreen().add_to(m)
                Geocoder_custom(collapsed=True, add_marker=True, suggestions=geocoder_vlastne_vyhladanie).add_to(m)
                folium.plugins.GroupedLayerControl(skupina_v_navigacii, exclusive_groups=False).add_to(m)
                folium.plugins.LocateControl(auto_start=False).add_to(m)
                Geoman().add_to(m)
                from draw_custom_administracia import Draw_custom_admin
                Draw_custom_admin(podskupiny=podskupiny_id_pre_pridavanie_objektu,export=False,draw_options= {"circle": False,"circlemarker": False}).add_to(m)

                return HttpResponse(m._repr_html_(), content_type="text/plain")

            if "daj_mapu_celu" in body and request.user.is_superuser:
                m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                               zoom_start=8,
                               width=1280, height=720,
                               prefer_canvas=False,
                               # crs="EPSG3857",

                               )

                geocoder_vlastne_vyhladanie = []
                skupiny_v_navigacii = dict()
                for skupina in Skupiny.objects.all().filter(spravca=None).order_by('priorita'):
                    _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
                    _skupina_v_mape.add_to(m)
                    podskupiny_v_mape = []
                    for podskupina in Podskupiny.objects.all().order_by('priorita'):
                        if (skupina.id == podskupina.skupina_id):
                            _podskupina_v_mape = folium.plugins.FeatureGroupSubGroup(_skupina_v_mape,
                                                                                     name=podskupina.meno)
                            _podskupina_v_mape.add_to(m)
                            pridaj_objekty_do_podskupiny(podskupina, _podskupina_v_mape, uzivatel=request.user,
                                                         geocoder=geocoder_vlastne_vyhladanie)
                            podskupiny_v_mape.append(_podskupina_v_mape)
                    skupiny_v_navigacii[skupina.meno] = podskupiny_v_mape

                # mapa nastavenie
                folium.plugins.Fullscreen().add_to(m)
                Geocoder_custom(collapsed=True, add_marker=True, suggestions=geocoder_vlastne_vyhladanie).add_to(m)
                folium.plugins.GroupedLayerControl(skupiny_v_navigacii, exclusive_groups=False).add_to(m)
                folium.plugins.LocateControl(auto_start=False).add_to(m)

                return HttpResponse(m._repr_html_(), content_type="text/plain")


            if "nova_skupina" in body and "nazov_skupiny" in body and "global_r" in body:
                if len(body["nazov_skupiny"]) ==0:
                    return HttpResponse(status=303)
                for skupina in Skupiny.objects.all():
                    if skupina.meno.lower() == str(body['nazov_skupiny']).lower():
                        return HttpResponse(status=304)
                nova_skupina = Skupiny()
                nova_skupina.meno = body['nazov_skupiny']
                nova_skupina.spravca = None
                viditelnost = Viditelnost_mapa()

                permisie_global = ""
                permisie_prihlaseny = ""
                if body['global_r']: permisie_global+="r"
                if body['global_w']: permisie_global += "w"
                if body['skupina_r']: permisie_prihlaseny += "r"
                if body['skupina_w']: permisie_prihlaseny += "w"
                if body['skupina_ignore']: permisie_prihlaseny =""
                viditelnost.globalne = permisie_global
                viditelnost.prihlaseny = permisie_prihlaseny
                viditelnost.save()
                nova_skupina.viditelnost = viditelnost
                nova_skupina.save()
                return HttpResponse(status=201)
            if "nova_podskupina" in body and "nazov_podskupiny" in body and "global_w" in body and "id_skupiny" in body:
                if len(body["nazov_podskupiny"]) ==0:
                    return HttpResponse(status=303)
                skupina = Skupiny.objects.get(id=body['id_skupiny'])
                for podskupina in Podskupiny.objects.filter(skupina=skupina):
                    if podskupina.meno.lower() == str(body['nazov_podskupiny']).lower():
                        return HttpResponse(status=304)
                nova_podskupina = Podskupiny()
                nova_podskupina.meno = body['nazov_podskupiny']


                viditelnost = Viditelnost_mapa()
                permisie_global = ""
                permisie_prihlaseny = ""
                if body['global_r']: permisie_global+="r"
                if body['global_w']: permisie_global += "w"
                if body['podskupina_r']: permisie_prihlaseny += "r"
                if body['podskupina_w']: permisie_prihlaseny += "w"
                if body['podskupina_ignore']: permisie_prihlaseny =""
                viditelnost.globalne = permisie_global
                viditelnost.prihlaseny = permisie_prihlaseny
                viditelnost.save()
                nova_podskupina.viditelnost = viditelnost
                nova_podskupina.spravca = None
                nova_podskupina.skupina=skupina
                nova_podskupina.save()
                return HttpResponse(status=201)
            if "admin_coord_update" in body and "geometry" in body and "id_objektu" in body and "style" in body and "update_pozicia" in body:
                objekt = Objekty.objects.get(id=body['id_objektu'])
                body['geometry']['coordinates'] = body['update_pozicia']
                objekt.geometry = GEOSGeometry(json.dumps(body['geometry']))
                objekt.style = body['style']
                if body.get('html')!="":
                    objekt.html = body.get('html')
                objekt.save()
                return HttpResponse(status=201)
            if "admin_delete_objekt" in body and "id_objektu" in body:
                for objekt_id in body.get('id_objektu'):
                    objekt = Objekty.objects.get(id=objekt_id)
                    if (objekt.nastavenia == None):
                        nastavenia = dict()
                        nastavenia["deleted"] = True
                    else:
                        nastavenia = json.loads(objekt.nastavenia)
                        nastavenia["deleted"] = True
                    objekt.nastavenia = json.dumps(nastavenia)
                    objekt.save()


                return HttpResponse(status=201)
            if "admin_object_create" in body and "coords" in body and "meno" in body and "podskupina_id" in body:
                geometria_cela = json.loads(body.get('coords'))
                novy_objekt = Objekty()
                novy_objekt.geometry = GEOSGeometry(json.dumps(geometria_cela.get('geometry')))
                novy_objekt.meno = body.get('meno')
                novy_objekt.podskupina = Podskupiny.objects.get(id=body['podskupina_id'])
                if body.get('stupen')!= '0':
                    novy_objekt.stupen_ochrany = int(body.get('stupen'))
                if body.get('diskusia'):
                    novy_objekt.diskusia = 1
                else:
                    novy_objekt.diskusia = 0
                novy_objekt.html = body.get('html')

                INSERT_STATEMENT = 'INSERT INTO objekty (meno,html,diskusia,podskupina,stupen_ochrany,geometry) VALUES (%s, %s,%s, %s, %s,ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)) RETURNING id;'
                cur.execute(INSERT_STATEMENT, (novy_objekt.meno, novy_objekt.html, novy_objekt.diskusia, novy_objekt.podskupina.id,novy_objekt.stupen_ochrany,str(json.loads(body.get('coords'))['geometry'])   ))

                return HttpResponse(status=201)
            if "update_viditelnost_skupina" in body and "skupina_id" in body and "global_read" in body and "global_write" in body and "uzivatelia" in body: #A mnoho ďalšiho :)
                if "update_viditelnost_podskupina" in body and body['update_viditelnost_podskupina']: #Funguje na skupiny aj podskupiny zároveň
                    skupina = Podskupiny.objects.get(id=body['skupina_id'])
                else:
                    skupina = Skupiny.objects.get(id=body['skupina_id'])
                viditelnost = skupina.viditelnost
                viditelnost.globalne=""
                viditelnost.prihlaseny = ""
                if body['global_read']:viditelnost.globalne+="r"

                if body['global_write']: viditelnost.globalne+="w"

                if body['prihlaseny_read']:viditelnost.prihlaseny+="r"

                if body['prihlaseny_write']:viditelnost.prihlaseny+="w"

                if body['prihlaseny_ignore']:
                    viditelnost.prihlaseny = ""

                body['uzivatelia'].extend(body['novy_uzivatelia'])
                for uzivatel in body['uzivatelia']:
                    permisie = ""
                    if uzivatel.get("read"): permisie+="r"
                    if uzivatel.get("write"):
                        notifikacia = Notifikacie()
                        notifikacia.odosielatel = User.objects.get(username=request.user.username)
                        notifikacia.prijimatel = User.objects.get(username=uzivatel.get('username'))
                        notifikacia.sprava = f"Bolo Vám udelené právo upravovať skupinu {skupina.meno}"
                        notifikacia.save()
                        permisie += "w"
                    if uzivatel.get('username') in viditelnost.uzivatelia and "w" not in permisie and "w" in viditelnost.uzivatelia[uzivatel.get('username')]:
                        notifikacia = Notifikacie()
                        notifikacia.odosielatel = User.objects.get(username=request.user.username)
                        notifikacia.prijimatel = User.objects.get(username=uzivatel.get('username'))
                        notifikacia.sprava = f"Bolo Vám zrušené právo upravovať skupinu {skupina.meno}"
                        notifikacia.save()
                    viditelnost.uzivatelia[uzivatel.get('username')] = permisie
                viditelnost.save()




            ##########Json upload / download vrstiev##########
            if "json_download" in body and "idcka_list" in body:
                zoznam_idcok_podskupiny =  body.get("idcka_list")
                zoznam_podskupin = []
                zoznam_skupin = []
                zoznam_viditelnost_skupiny = []
                zoznam_viditelnost_podskupiny = []
                zoznam_objekty = []
                for idcko in zoznam_idcok_podskupiny:
                    podskupina = Podskupiny.objects.get(id=idcko)
                    zoznam_podskupin.append(podskupina.id)
                    zoznam_viditelnost_podskupiny.append(podskupina.viditelnost.id)
                    if podskupina.skupina not in zoznam_skupin:
                        zoznam_skupin.append(podskupina.skupina.id)
                        zoznam_viditelnost_skupiny.append(podskupina.skupina.viditelnost.id)
                    for objekt in Objekty.objects.filter(podskupina_id=podskupina.id):
                        zoznam_objekty.append(objekt.id)
                vysledny_json = dict()

                json_serializer = json_ser.Serializer()
                vysledny_json['skupiny'] = json_serializer.serialize(Skupiny.objects.filter(id__in=zoznam_skupin),ensure_ascii=False)
                vysledny_json['skupiny_viditelnost'] = json_serializer.serialize(Viditelnost_mapa.objects.filter(id__in=zoznam_viditelnost_skupiny),ensure_ascii=False)
                vysledny_json['podskupiny'] = json_serializer.serialize(Podskupiny.objects.filter(id__in=zoznam_podskupin),ensure_ascii=False)
                vysledny_json['podskupiny_viditelnost'] = json_serializer.serialize(Viditelnost_mapa.objects.filter(id__in=zoznam_viditelnost_podskupiny),ensure_ascii=False)
                vysledny_json['objekty'] = json_serializer.serialize(Objekty.objects.filter(id__in=zoznam_objekty),ensure_ascii=False)
                response = HttpResponse(json.dumps(vysledny_json,ensure_ascii=False), content_type='application/json')
                response['Content-Disposition'] = 'attachment; filename=export.json'
                return response


        except:
            traceback.print_exc()
            return HttpResponse(status=500)


    return HttpResponse(status=204)


@csrf_exempt
def api_request_file(request):
    if request.user.is_superuser==False: return HttpResponse(status=304) #neautorizovaný
    if request.method == 'POST':
        try:
                #ešte dorobiť viditelnosť
                if "json_admin_subor_send" in request.POST:

                    try:
                        file = request.FILES['file']
                        data = file.read()
                        json_data = json.dumps(data.decode(),ensure_ascii=False)
                        hotovy_json = json.loads(json.loads(json_data))
                        skupiny =  json_ser.Deserializer(hotovy_json['skupiny'])
                        skupiny_viditelnost = json_ser.Deserializer(hotovy_json['skupiny_viditelnost'])
                        podskupiny = json_ser.Deserializer(hotovy_json['podskupiny'])
                        podskupiny_viditelnost = json_ser.Deserializer(hotovy_json['podskupiny_viditelnost'])
                        objekty = json_ser.Deserializer(hotovy_json['objekty'])
                    except:
                        #print("Padol som")
                        return HttpResponse(status=303) #Ak chyba, tak vyhod modal

                    for viditelnost_pre_skupinu in skupiny_viditelnost:
                        viditelnost_pre_skupinu.save()

                    for skupina in skupiny:
                        skupina.save()

                    for viditelnost_pre_podskupinu in podskupiny_viditelnost:
                        viditelnost_pre_podskupinu.save()

                    for podskupina in podskupiny:
                        podskupina.save()

                    for objekt in objekty:
                        objekt.save()
        except:
            traceback.print_exc()
            return HttpResponse(status=500)

    return HttpResponse(status=204)


@login_required
def administracia(request):
    if navbar_zapni_administraciu(request.user)==False: #Ak nemám žiadne oprávnenie ....
        return redirect('/')
    context = {}
    vsetky_systemove_skupiny = []
    podskupiny_sys_skupin = dict()
    for skupina in Skupiny.objects.filter(spravca=None).order_by('priorita'):
        permisie_skupina = False
        permisie_skupina_temp = False
        if over_viditelnost(skupina.viditelnost,request.user.is_authenticated,request.user.username,"w") or request.user.is_superuser:
            permisie_skupina = True
        podskupiny = []
        for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
            permisie_podskupina = False
            if(permisie_skupina): permisie_podskupina=True
            if over_viditelnost(podskupina.viditelnost, request.user.is_authenticated, request.user.username,"w") or request.user.is_superuser:
                permisie_podskupina = True
                permisie_skupina_temp = True
            podskupiny.append( (podskupina,permisie_podskupina) )

        if permisie_skupina or permisie_skupina_temp:
            vsetky_systemove_skupiny.append((skupina, permisie_skupina,permisie_skupina_temp))

        podskupiny_sys_skupin[skupina.id] = podskupiny
    context['sys_skupiny_list'] = vsetky_systemove_skupiny
    context['sys_podskupiny_dict'] = podskupiny_sys_skupin
    context['get_data'] = dict(request.GET.items())
    context['vsetci_uzivatelia'] = User.objects.values()

    return render(request, 'administration/admin.html',context)

@login_required
def administracia_json(request):
    if request.user.is_superuser == False:
        return redirect('/administracia')
    context = {}
    vsetky_systemove_skupiny = []
    podskupiny_sys_skupin = dict()
    for skupina in Skupiny.objects.filter(spravca=None).order_by('priorita'):
        vsetky_systemove_skupiny.append(skupina)
        podskupiny = []
        for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
            podskupiny.append(podskupina)
        podskupiny_sys_skupin[skupina.id] = podskupiny
    context['sys_skupiny_list'] = vsetky_systemove_skupiny
    context['sys_podskupiny_dict'] = podskupiny_sys_skupin



    return render(request, 'administration/json.html',context)


@login_required
def user_bin(request):
    context = {}
    vysledok = []
    for objekt in Objekty.objects.filter(nastavenia__isnull=False,podskupina__spravca__isnull=False,podskupina__spravca=request.user.username):
        nastavenia = json.loads(objekt.nastavenia)
        if "deleted" not in nastavenia:
            continue
        elif "deleted" in nastavenia and nastavenia["deleted"]!=True:
            continue
        podskupina = objekt.podskupina
        skupina = podskupina.skupina
        vysledok.append(  (skupina,podskupina,objekt)  )
    context['kos'] = vysledok
    context['navbar_administracia'] = navbar_zapni_administraciu(request.user)
    return render(request, 'kos/kos.html',context)

@login_required
def admin_bin(request):
    if navbar_zapni_administraciu(request.user)==False: #Ak nemám žiadne oprávnenie ....
        return redirect('/')
    if request.user.is_superuser == False:
        return redirect('/administracia')
    context = {}
    vysledok = []
    for objekt in Objekty.objects.filter(nastavenia__isnull=False,podskupina__spravca__isnull=True):
        nastavenia = json.loads(objekt.nastavenia)
        if "deleted" not in nastavenia:
            continue
        elif "deleted" in nastavenia and nastavenia["deleted"]!=True:
            continue
        podskupina = objekt.podskupina
        skupina = podskupina.skupina
        vysledok.append(  (skupina,podskupina,objekt)  )
    context['kos'] = vysledok

    return render(request, 'administration/bin.html',context)


@login_required
def test(request):
    if request.user.is_superuser == False:
        return redirect('/')
    context = {}
    m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                   zoom_start=10,
                   width=1280, height=720,
                   prefer_canvas=False,
                   # crs="EPSG3857",

                   )
    html = """
        <script src="https://unpkg.com/htmx.org@1.9.8" integrity="sha384-rgjA7mptc2ETQqXoYC3/zJvkU7K/aP44Y+z7xQuJiVnB/422P/Ak+F/AqFR7E4Wr" crossorigin="anonymous"></script>
          <button hx-post="/clicked" hx-swap="outerHTML">
            Click Me
          </button>
        <h1> This popup is an Iframe</h1><br>
        With a few lines of code...
        <p>
        <code>
            from numpy import *<br>
            exp(-2*pi)
        </code>
        </p>
        """

    html = """
    
            <b>PR Štokeravská vápenka</b><br> 
            IV. stupeň ochrany<br> 
                <a href="https://www.slovensko.sk/sk/agendy/agenda/_narodne-parky-a-prirodne-rezer/" target="_blank" rel="noopener noreferrer">Pravidlá v tejto oblasti</a>
                <br>       
        <button onlick="uprav_uzivatelsku_vrstvu('Ano','admin');"></button>
        <script>
                async function uprav_uzivatelsku_vrstvu(id,meno) {
                  let user = {
                  id: id,
                  username: meno,
                  uprav_vrstvu_iframe: null
                };

                let response = await fetch('/api', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json;charset=utf-8'
                  },
                  body: JSON.stringify(user)
                });

           return true;
        }
            </script>
    """
    

    iframe = branca.element.IFrame(html=html, width=500, height=300)
    #popup = folium.Popup(folium.Html(html, script=True), lazy=False)
    popup = folium.Popup(iframe, max_width=500)
    folium.Marker(
        location=[48.73044030054515, 19.456582270083356],
        tooltip="Click me!",
        popup=popup,
        icon=folium.Icon(icon="cloud"),
    ).add_to(m)
    context['m'] = m._repr_html_()
    return render(request, 'test/test.html', context)

@csrf_exempt
def htmx_request(request):
    #<button hx-post="http://127.0.0.1:8000/htmx/?username={uzivatel.username}&request=zdielanie_list" hx-swap="outerHTML">
    html = ""
    if "request" not in request.GET:
        return HttpResponse("Chýba požiadavka, skúste znova")
    poziadavka = request.GET.get('request')
    try:
        user = User.objects.get(username=request.GET.get('username'))

        if poziadavka == "zdielanie_list" and "objekt" in request.GET:
            objekt = Objekty.objects.get(id=request.GET.get('objekt'))
            if objekt.nastavenia!= None:
                nastavenia = json.loads(objekt.nastavenia)
            else:
                nastavenia = None
            zoznam_priatelov = Friend.objects.friends(user)
            for priatel in zoznam_priatelov:
                if Block.objects.is_blocked(user, priatel) == True:
                    zoznam_priatelov.remove(priatel)
            if(len(zoznam_priatelov)==0):
                return HttpResponse("Nemáte žiadnych priateľov s ktorými by sa objekt dal zdieľať")
            html = ""
            html+="""<ul class="list-group">"""
            for priatel in zoznam_priatelov:
                if nastavenia != None and "shared_with" in nastavenia and priatel.username in nastavenia["shared_with"]:
                    html+= f"""<li class="list-group-item py-1 px-1">{priatel.username} <a href="#" hx-post="http://127.0.0.1:8000/htmx/?username={user.username}&request=zrusit_zdielanie&objekt={objekt.id}&zdielane_s={priatel.username}" hx-swap="outerHTML" style="margin:5px;">Zrušiť zdieľanie</a></li>"""
                else:
                    html += f"""<li class="list-group-item py-1 px-1">{priatel.username} <a href="#" hx-post="http://127.0.0.1:8000/htmx/?username={user.username}&request=zdielat&objekt={objekt.id}&zdielane_s={priatel.username}" hx-swap="outerHTML" style="margin:5px;">Zdieľať</a></li>"""

            html+="</ul>"
        if poziadavka == "zdielat" and "objekt" in request.GET and "zdielane_s" in request.GET:
            zdielany_objekt = Objekty.objects.get(id=request.GET.get('objekt'))
            priatel = User.objects.get(username=request.GET.get('zdielane_s')).username #!!!
            viditelnost = Viditelnost_mapa()
            viditelnost.uzivatelia[priatel] = "r"
            viditelnost.save()
            nova_podskupina_zdielaneho_objektu = pridaj_podskupinu(zdielany_objekt.meno, viditelnost.id,
                                                                   priatel,
                                                                   vrat_skupinu_s_uzivatelom_zdielanych_objektov(
                                                                       priatel))
            if (zdielany_objekt.nastavenia == None):
                nastavenia = dict()
                nastavenia["shared_with"] = dict()
                nastavenia["shared_with"][priatel] = nova_podskupina_zdielaneho_objektu
            elif "shared_with" in zdielany_objekt.nastavenia:
                nastavenia = json.loads(zdielany_objekt.nastavenia)
                nastavenia["shared_with"][priatel] = nova_podskupina_zdielaneho_objektu
            else:
                nastavenia = json.loads(zdielany_objekt.nastavenia)
                nastavenia["shared_with"] = dict()
                nastavenia["shared_with"][priatel] = nova_podskupina_zdielaneho_objektu
            zdielany_objekt.nastavenia = json.dumps(nastavenia)
            zdielany_objekt.save()
            notifikacia = Notifikacie()
            notifikacia.prijimatel = User.objects.get(username=request.GET.get('zdielane_s'))
            notifikacia.odosielatel = User.objects.get(username=zdielany_objekt.podskupina.spravca)
            notifikacia.sprava = f"s Vami zdieľa objekt <b>{zdielany_objekt.meno}</b>"
            notifikacia.save()


            return HttpResponse(f"""<a href="#" hx-post="http://127.0.0.1:8000/htmx/?username={user.username}&request=zrusit_zdielanie&objekt={zdielany_objekt.id}&zdielane_s={priatel}" hx-swap="outerHTML" style="margin:5px;">Zrušiť zdieľanie</a>""")

        if poziadavka == "zrusit_zdielanie" and "objekt" in request.GET and "zdielane_s" in request.GET:
            zdielany_objekt = Objekty.objects.get(id=request.GET.get('objekt'))
            priatel = User.objects.get(username=request.GET.get('zdielane_s')).username #!!!
            nastavenia = json.loads(zdielany_objekt.nastavenia)
            if "shared_with" in nastavenia and (priatel in nastavenia["shared_with"]):
                Podskupiny.objects.get(id=nastavenia["shared_with"][priatel]).delete()
                nastavenia["shared_with"].pop(priatel)
                zdielany_objekt.nastavenia = json.dumps(nastavenia)
                zdielany_objekt.save()
            if "ifrejm" in request.GET:
                return HttpResponse(
                    f"""Zdieľanie objektu úspešne zrušené, zmena sa prejaví po znovunačítaní mapy""")
            return HttpResponse(f"""<a href="#" hx-post="http://127.0.0.1:8000/htmx/?username={user.username}&request=zdielat&objekt={zdielany_objekt.id}&zdielane_s={priatel}" hx-swap="outerHTML" style="margin:5px;">Zdieľať</a>""")

    except:
        traceback.print_exc()
        return HttpResponse("Niekde nastala chyba, skúste znova")

    response = HttpResponse(html)
    return response