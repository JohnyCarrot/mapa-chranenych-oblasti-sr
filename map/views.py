from django.shortcuts import render
import folium
import time
import geocoder
import random
import json
from folium import plugins
from django.db import connection
from draw_custom import Draw as Draw_custom
from django.shortcuts import render, redirect
from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from friendship.models import Friend, Follow, Block, FriendshipRequest, FriendshipManager
from django.http import HttpResponseRedirect
from .models import Skupiny,Podskupiny,Objekty
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

def zdielat_objekt_html_list(uzivatel,objekt_id):
    html=""
    objekt = Objekty.objects.get(id=objekt_id)
    for priatel in Friend.objects.friends(uzivatel):
        html+=f"""
        {priatel.username} <a href="?object_share={objekt_id}&username={priatel.username}&objectname={objekt.meno}" target="_top" class="button">Zdieľať</a> <br> 
        """

    return html



def pridaj_objekty_do_podskupiny(podskupina,podskupina_v_mape, uzivatel = None):
    for objekt in Objekty.objects.all():
        nastavenia = None
        zdielane = False
        if(objekt.nastavenia != None and uzivatel!= None):
            nastavenia = json.loads(objekt.nastavenia)
            if"shared_with" in nastavenia and uzivatel.username in nastavenia["shared_with"] and nastavenia["shared_with"][uzivatel.username]==podskupina.id:
                zdielane = True
        if(objekt.podskupina_id!=podskupina.id and zdielane == False):
            continue
        html = objekt.html
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
        folium.GeoJson(GEOSGeometry(objekt.geometry).json, style_function=lambda x, fillColor=objekt.fillcolor, color=objekt.color: {
        "fillColor": fillColor,
        "color": color,
    }).add_to(podskupina_v_mape).add_child(
            folium.Popup(folium.Html(html,script=True),lazy=False))

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
        INSERT_STATEMENT = 'INSERT INTO objekty (meno, color, fillcolor,html,diskusia,podskupina,geometry) VALUES (%s, %s, %s,%s, %s, %s,ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)) RETURNING id;'
        cur.execute(INSERT_STATEMENT, (requests.GET.get('new_object_name'),"white","white","",0,podskupina_noveho_objektu.id,str(dictData['geometry'])   )  )
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
    m = folium.Map(location=[48.73044030054515, 19.456582270083356],
                   zoom_start=9,
                   width=1000, height=800,
                   prefer_canvas=True,
                   # crs="EPSG3857",

                   )
    skupiny_v_navigacii = dict()
    for skupina in Skupiny.objects.all():
        if over_viditelnost(skupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username)):
            _skupina_v_mape = folium.FeatureGroup(skupina.meno, control=False)
            _skupina_v_mape.add_to(m)
            podskupiny_v_mape = []
            for podskupina in Podskupiny.objects.all():
                if(skupina.id ==podskupina.skupina_id and over_viditelnost(podskupina.viditelnost,prihlaseny=requests.user.is_authenticated,username=str(requests.user.username))):
                    _podskupina_v_mape = folium.plugins.FeatureGroupSubGroup(_skupina_v_mape, name=podskupina.meno)
                    _podskupina_v_mape.add_to(m)
                    pridaj_objekty_do_podskupiny(podskupina,_podskupina_v_mape,uzivatel=requests.user)
                    podskupiny_v_mape.append(_podskupina_v_mape)
            skupiny_v_navigacii[skupina.meno] = podskupiny_v_mape
    print(f"---Všetky objekty v db: %s seconds ---" % (time.time() - start_time_temp))

    start_time_temp = time.time()



    # mapa nastavenie
    folium.plugins.Fullscreen().add_to(m)
    folium.plugins.Geocoder(collapsed=True, add_marker=True).add_to(m)
    folium.plugins.GroupedLayerControl(skupiny_v_navigacii, exclusive_groups=False).add_to(m)
    folium.plugins.LocateControl(auto_start=True).add_to(m)
    if(requests.user.is_authenticated):
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
