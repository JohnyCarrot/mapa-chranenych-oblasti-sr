import traceback

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import folium
import time
import geocoder
import random
import json

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
from .models import Skupiny,Podskupiny,Objekty, Profile
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
        styl={}
        if objekt.style== None:
            styl = {}
        else:
            styl = objekt.style
        folium.GeoJson(geometria_cela, style_function=lambda x: styl,name=objekt.meno).add_to(podskupina_v_mape).add_child(
            folium.Popup(folium.Html(html,script=True),lazy=False))
        geocoder.append({"name":objekt.meno,"center":[geometria.centroid.coord_seq.getY(0),geometria.centroid.coord_seq.getX(0)]})



def over_viditelnost(viditelnost,prihlaseny = False,username = ""):
    if viditelnost == None: return False
    if("*" in viditelnost): return True
    if("+" in viditelnost and prihlaseny):return True
    if(prihlaseny and username in viditelnost):
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
            pridaj_skupinu("Vlastné objekty",requests.user.username,[requests.user.username],nastavenia = json.dumps({'own': None,}))
        if vrat_skupinu_s_uzivatelom_zdielanych_objektov(requests.user.username) == None:
            pridaj_skupinu("So mnou zdieľané objekty",requests.user.username,[requests.user.username],nastavenia = json.dumps({'shared': None,}))
    #Pridanie objektu užívateľom:
    if (requests.user.is_authenticated and requests.GET.get('new_object') != None and requests.GET.get('new_object_name')!=None):
        dictData = json.loads(requests.GET.get('new_object'))
        podskupina_noveho_objektu = Podskupiny()
        podskupina_noveho_objektu.meno = requests.GET.get('new_object_name')
        podskupina_noveho_objektu.viditelnost = [requests.user.username]
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
        nova_podskupina_zdielaneho_objektu = pridaj_podskupinu(requests.GET.get('objectname'),[priatel],priatel,vrat_skupinu_s_uzivatelom_zdielanych_objektov(priatel))
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
                   zoom_start=9,
                   width=1000, height=800,
                   prefer_canvas=False,
                   # crs="EPSG3857",

                   )
    geocoder_vlastne_vyhladanie = []
    skupiny_v_navigacii = dict()
    for skupina in Skupiny.objects.all().order_by('priorita'):
        if over_viditelnost(skupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username)):
            _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
            _skupina_v_mape.add_to(m)
            podskupiny_v_mape = []
            for podskupina in Podskupiny.objects.all().order_by('priorita'):
                if(skupina.id ==podskupina.skupina_id and over_viditelnost(podskupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username))):
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
    folium.plugins.LocateControl(auto_start=True).add_to(m)
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
    print(f"---Generacia mapy: %s seconds ---" % (time.time() - start_time_temp))
    print(f"---celá stránka %s seconds ---" % (time.time() - start_time))
    #print("Počet znakov v html: "+str(len(m)))
    return render(requests, 'index.html', context)


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

    return render(requests, 'friends/index.html',context)


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            vlastne_objekty_skupina = pridaj_skupinu("Vlastné objekty",user.username,[user.username],nastavenia = json.dumps({'own': None,}))
            zdielane_objekty_podskupina = pridaj_skupinu("So mnou zdieľané objekty",user.username,[user.username],nastavenia = json.dumps({'shared': None,}))
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
            if request.user.is_superuser and "podskupina" in body and "id" in body and "priorita" in body:
                podskupina = Podskupiny.objects.get(id=body['id'])
                podskupina.priorita = body['priorita']
                podskupina.save()
                return HttpResponse(status=202)
            if request.user.is_superuser and "skupina" in body and "id" in body and "priorita" in body:
                skupina = Skupiny.objects.get(id=body['id'])
                skupina.priorita = body['priorita']
                skupina.save()
                return HttpResponse(status=202)
            if request.user.is_superuser and "daj_mapu" in body and "id" in body and "skupina" in body:
                m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                               zoom_start=9,
                               width=1280, height=720,
                               prefer_canvas=False,
                               # crs="EPSG3857",

                               )
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
                    skupina_v_navigacii[skupina.meno] = podskupiny_v_mape
                else:
                    podskupina = Podskupiny.objects.get(id=body['id'])
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
                folium.plugins.LocateControl(auto_start=True).add_to(m)
                Geoman().add_to(m)


                return HttpResponse(m._repr_html_(), content_type="text/plain")
            if request.user.is_superuser and "nova_skupina" in body and "nazov_skupiny" in body and "viditelnost" in body:
                if len(body["nazov_skupiny"]) ==0:
                    return HttpResponse(status=303)
                for skupina in Skupiny.objects.all():
                    if skupina.meno.lower() == str(body['nazov_skupiny']).lower():
                        return HttpResponse(status=304)
                nova_skupina = Skupiny()
                nova_skupina.meno = body['nazov_skupiny']
                if body['viditelnost']==[]:
                    body['viditelnost'] = ['*']
                nova_skupina.viditelnost = body['viditelnost']
                nova_skupina.spravca = None
                nova_skupina.save()
                return HttpResponse(status=201)
            if request.user.is_superuser and "nova_podskupina" in body and "nazov_podskupiny" in body and "viditelnost" in body and "id_skupiny" in body:
                if len(body["nazov_podskupiny"]) ==0:
                    return HttpResponse(status=303)
                skupina = Skupiny.objects.get(id=body['id_skupiny'])
                for podskupina in Podskupiny.objects.filter(skupina=skupina):
                    if podskupina.meno.lower() == str(body['nazov_podskupiny']).lower():
                        return HttpResponse(status=304)
                nova_podskupina = Podskupiny()
                nova_podskupina.meno = body['nazov_podskupiny']
                if body['viditelnost'] == []:
                    body['viditelnost'] = ['*']
                nova_podskupina.viditelnost = body['viditelnost']
                nova_podskupina.spravca = None
                nova_podskupina.skupina=skupina
                nova_podskupina.save()
                return HttpResponse(status=201)
            if request.user.is_superuser and "admin_coord_update" in body and "geometry" in body and "id_objektu" in body and "style" in body and "update_pozicia" in body:
                objekt = Objekty.objects.get(id=body['id_objektu'])
                body['geometry']['coordinates'] = body['update_pozicia']
                objekt.geometry = GEOSGeometry(json.dumps(body['geometry']))
                objekt.style = body['style']
                objekt.save()
                return HttpResponse(status=201)
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
        vsetky_systemove_skupiny.append(skupina)
        podskupiny = []
        for podskupina in Podskupiny.objects.filter(skupina=skupina).order_by('priorita'):
            podskupiny.append(podskupina)
        podskupiny_sys_skupin[skupina.id] = podskupiny
    context['sys_skupiny_list'] = vsetky_systemove_skupiny
    context['sys_podskupiny_dict'] = podskupiny_sys_skupin
    context['get_data'] = dict(request.GET.items())

    return render(request, 'administration/admin.html',context)
