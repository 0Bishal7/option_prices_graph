from django.urls import path,re_path
from straddle.consumers import StraddleConsumer

websocket_urlpatterns = [
    path("ws/straddle/", StraddleConsumer.as_asgi()),
    # re_path(r"ws/straddle/(?P<symbol>\w+)/$", StraddleConsumer.as_asgi()),

]
