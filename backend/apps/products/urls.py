from rest_framework.routers import SimpleRouter

from .views import FridgeItemViewSet

router = SimpleRouter()
router.register(
    r"fridges/(?P<fridge_id>[0-9a-fA-F-]{36})/items",
    FridgeItemViewSet,
    basename="fridge-item",
)

urlpatterns = router.urls
