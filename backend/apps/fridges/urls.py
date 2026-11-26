from rest_framework.routers import SimpleRouter

from .views import FridgeViewSet

router = SimpleRouter()
router.register("fridges", FridgeViewSet, basename="fridge")

urlpatterns = router.urls
