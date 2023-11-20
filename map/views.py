import traceback

import branca
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import folium
import time
import geocoder
import random
import json
from django.core.serializers import json as json_ser
from django.views.decorators.csrf import csrf_exempt
from folium import plugins
from django.db import connection
from draw_custom import Draw as Draw_custom
from geoman import Geoman as Geoman
from geocoder_custom import Geocoder as Geocoder_custom
from easy_button_non_universal import EasyButton as EasyButton
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from friendship.models import Friend, Follow, Block, FriendshipRequest, FriendshipManager
from django.http import HttpResponseRedirect, HttpResponse
from .models import Skupiny,Podskupiny,Objekty, Profile, Viditelnost_mapa, Notifikacie
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
    #if user.is_authenticated == False:
        #return False
    if user.is_superuser: return True
    for skupina in Skupiny.objects.filter(spravca=None).order_by('priorita'):
        permisie_skupina = False
        permisie_skupina_temp = False
        if over_viditelnost(skupina.viditelnost,user.is_authenticated,user.username,"w") or user.is_superuser:
            permisie_skupina = True

        for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
            if over_viditelnost(podskupina.viditelnost, user.is_authenticated, user.username,"w") or user.is_superuser:
                permisie_skupina_temp = True

        if permisie_skupina or permisie_skupina_temp:
            return True
    return False

def zdielat_objekt_html_list(uzivatel,objekt_id):
    html=""
    objekt = Objekty.objects.get(id=objekt_id)
    for priatel in Friend.objects.friends(uzivatel):
        if objekt_id in [x.id for x in vrat_zdielane_objekty_s_uzivatelom(priatel.username)]:
            html += f"""
            {priatel.username} <a href="?object_unshare={objekt_id}&username={priatel.username}&objectname={objekt.meno}" target="_top" class="button">Zrušiť zdielanie</a> <br> 
            """
        else:
            html+=f"""
            {priatel.username} <a href="?object_share={objekt_id}&username={priatel.username}&objectname={objekt.meno}" target="_top" class="button">Zdieľať</a> <br> 
            """
    return html


def pridaj_objekty_do_podskupiny(podskupina,podskupina_v_mape,geocoder, uzivatel = None):
    if(uzivatel == None or uzivatel.is_authenticated == False):
        nastavenie_mapy = None
    else:
        profil = Profile.objects.get(user_id=uzivatel.id)
        nastavenie_mapy = profil.map_settings
    for objekt in Objekty.objects.all():
        nastavenia = None
        zdielane = False
        if(sulad_s_nastavenim_mapy(nastavenie_mapy,objekt)==False):
            continue
        html = objekt.html
        if(objekt.nastavenia != None and uzivatel!= None):
            nastavenia = json.loads(objekt.nastavenia)
            if"shared_with" in nastavenia and uzivatel.username in nastavenia["shared_with"] and nastavenia["shared_with"][uzivatel.username]==podskupina.id:
                zdielane = True
                html+=f"""<p style="white-space: nowrap">Zdieľané používateľom: <b>{objekt.podskupina.spravca}</b></p>"""
                html += f"""<a href="?object_unshare={objekt.id}&username={uzivatel.username}&objectname={objekt.meno}" target="_top" class="button">Zrušiť zdielanie</a> <br> """
        if(objekt.podskupina_id!=podskupina.id and zdielane == False):
            continue
        if (objekt.diskusia == 1): html+=f"""<a href="forum/{objekt.id}" target="_blank" rel="noopener noreferrer">Diskusia</a>"""
        if(uzivatel!= None and zdielane == False and podskupina.spravca == uzivatel.username):
            html+= f"""<a href="spravuj?={objekt.id}" target="_blank" rel="noopener noreferrer">Upraviť</a><br>"""
            html+="""<iframe
              srcdoc='
                <html>
                  <head>
                    <style>
                      .toggle-button {
                        cursor: pointer;
                      }
                      
                      .toggle-button:hover {
                        text-decoration: underline;
                      }
                      
                      .toggle-button:focus {
                        outline: none;
                      }
                      
                      .toggle-content {
                        max-height: 0;
                        overflow: hidden;
                        transition: max-height 0.5s ease-out;
                      }
                      
                      .toggle-content.show {
                        max-height: 1000px;
                        transition: max-height 0.5s ease-in;
                      }
                    </style>
                  </head>
                  <body>
                    <button class="toggle-button" onclick="document.querySelector(&#x27;.toggle-content&#x27;).classList.toggle(&#x27;show&#x27;)">Zdieľať</button>
                    <div class="toggle-content">
                      <p>Vyberte užívateľa s ktorým chcete objekt zdieľať:</p>
                      %s
                    </div>
                  </body>
                </html>'
            ></iframe>
            """ % (zdielat_objekt_html_list(uzivatel,objekt.id))
        geometria = GEOSGeometry(objekt.geometry)
        geometria_cela = json.loads(geometria.json)
        geometria_cela['serverID'] = objekt.id
        geometria_cela['popup_HTML'] = objekt.html

        if objekt.style== None:
            objekt.style={}
            objekt.save()
        styl = objekt.style
        folium.GeoJson(geometria_cela, style_function=lambda x, styl=styl: styl,name=objekt.meno).add_to(podskupina_v_mape).add_child(
            folium.Popup(folium.Html(html,script=True),lazy=False))
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
    start_time = time.time()
    start_time_temp = time.time()
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
    #Zdielanie objektu
    if (requests.user.is_authenticated and requests.GET.get('object_share') != None and requests.GET.get('username') != None and requests.GET.get('objectname')!= None):
        zdielany_objekt = Objekty.objects.get(id=requests.GET.get('object_share'))
        priatel = requests.GET.get('username')
        viditelnost = Viditelnost_mapa()
        viditelnost.uzivatelia[priatel] = "r"
        viditelnost.save()
        nova_podskupina_zdielaneho_objektu = pridaj_podskupinu(requests.GET.get('objectname'),viditelnost.id,priatel,vrat_skupinu_s_uzivatelom_zdielanych_objektov(priatel))
        if(zdielany_objekt.nastavenia==None):
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
        return HttpResponseRedirect(requests.path_info)
    # Zrušenie zdielania objektu

    if (requests.user.is_authenticated and requests.GET.get('object_unshare') != None and requests.GET.get('username') != None and requests.GET.get('objectname') != None):
        priatel = requests.GET.get('username')
        zdielany_objekt = Objekty.objects.get(id=requests.GET.get('object_unshare'))
        nastavenia = json.loads(zdielany_objekt.nastavenia)
        if "shared_with" in nastavenia and (priatel in nastavenia["shared_with"]):
            Podskupiny.objects.get(id=nastavenia["shared_with"][priatel]).delete()
            nastavenia["shared_with"].pop(priatel)
            zdielany_objekt.nastavenia = json.dumps(nastavenia)
            zdielany_objekt.save()
        return HttpResponseRedirect(requests.path_info)

    #Normálne načítanie
    m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                   zoom_start=8,
                   width=1000, height=800,
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
        Draw_custom(export=False,draw_options= {"circle": False,"circlemarker": False}).add_to(m)
    print(f"---Pluginy: %s seconds ---" % (time.time() - start_time_temp))
    start_time_temp = time.time()
    m = m._repr_html_()
    context = {
        'm': m,
    }

    context['navbar_administracia'] = navbar_zapni_administraciu(requests.user) #Neoverovať prihlásenie !!!
    print(f"---Generacia mapy: %s seconds ---" % (time.time() - start_time_temp))
    print(f"---celá stránka %s seconds ---" % (time.time() - start_time))
    #print("Počet znakov v html: "+str(len(m)))
    return render(requests, 'index/index.html', context)


# Koniec mapy, začiatok diskusného fóra
def forum(requests):
    return render(requests, 'forum/index.html')

# Editacia objektov
def subgroup_edit(requests):

    return render(requests, 'spravuj_podskupiny/index.html')

def friends_main_page(requests):
    if requests.user.is_authenticated == False:
        return render(requests, 'friends/index.html')
    context = {}
    user_search = []
    if(requests.GET.get('search') != None):
        for i in get_user_model().objects.all():
            uz_odoslane = False  # kontrola, či už náhodou žiadosť nebola poslaná
            if Friend.objects.are_friends(requests.user, i) == True:
                continue #Ak sú priatelia nechcem ho vo vyhladávaní
            if (requests.user.get_username()==i.get_username()):
                continue
            if str(i.get_username()).startswith(requests.GET.get('search')):
                for x in Friend.objects.sent_requests(user=requests.user):
                    if(User.objects.get(id=x.to_user_id).get_username() == i.get_username()):
                        uz_odoslane = True
                user_search.append(   (str(i.get_username()),uz_odoslane)  )
    context['user_search'] = user_search
    if (requests.GET.get('friendship_request') != None):
        other_user = User.objects.get(username=requests.GET.get('friendship_request'))
        Friend.objects.add_friend(
            requests.user,
            other_user)
    if (requests.GET.get('cancel_friendship_request') != None):
        other_user = User.objects.get(username=requests.GET.get('cancel_friendship_request'))
        for x in Friend.objects.sent_requests(user=requests.user):
            if (User.objects.get(id=x.to_user_id).get_username() == other_user.get_username()):
                x.cancel()
    if (requests.GET.get('friendship_accept') != None):
        other_user = User.objects.get(username=requests.GET.get('friendship_accept'))
        for x in Friend.objects.unrejected_requests(user=requests.user):
            if (User.objects.get(id=x.from_user_id).get_username() == other_user.get_username()):
                x.accept()
    if (requests.GET.get('friendship_reject') != None):
        other_user = User.objects.get(username=requests.GET.get('friendship_reject'))
        for x in Friend.objects.unrejected_requests(user=requests.user):
            if (User.objects.get(id=x.from_user_id).get_username() == other_user.get_username()):
                x.reject()

    context["all_friends"] = Friend.objects.friends(requests.user)
    context["all_unread_friend_requests"] = Friend.objects.unrejected_requests(user=requests.user)

    context['navbar_administracia'] = navbar_zapni_administraciu(requests.user)
    return render(requests, 'friends/index.html',context)


def register_request(request):
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
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request=request, template_name="main/register.html", context={"register_form": form})

@csrf_exempt
def api_request(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            profil = Profile.objects.get(user_id=request.user.id)
            if("stupen2" in body and "stupen3" in body and "stupen4" in body and "stupen5" in body):
                mapa_nastavenia = profil.map_settings
                mapa_nastavenia.stupen2 = body['stupen2']
                mapa_nastavenia.stupen3 = body['stupen3']
                mapa_nastavenia.stupen4 = body['stupen4']
                mapa_nastavenia.stupen5 = body['stupen5']
                mapa_nastavenia.save()
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
                    objekt = Objekty(id=objekt_id)
                    objekt.delete()
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
                    if uzivatel.get("write"): permisie += "w"
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

    if len(vsetky_systemove_skupiny) ==0: #Ak nemám žiadne oprávnenie ....
        return redirect('/')

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

    iframe = branca.element.IFrame(html=html, width=500, height=300)
    popup = folium.Popup(iframe, max_width=500)
    folium.Marker(
        location=[48.73044030054515, 19.456582270083356],
        tooltip="Click me!",
        popup=popup,
        icon=folium.Icon(icon="cloud"),
    ).add_to(m)
    context['m'] = m._repr_html_()
    return render(request, 'test/test.html', context)
