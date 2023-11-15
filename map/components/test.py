from django_unicorn.components import UnicornView


class TestView(UnicornView):

    def mount(self):
        pass

    def vypis(self):
        print("Ahoj")
