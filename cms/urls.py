from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cms import views

router = DefaultRouter()
router.register(r"pages", views.PageViewSet, basename="pages")
router.register(r"html-blocks", views.BlockHTMLViewSet, basename="html-blocks")
router.register(r"markdown-blocks", views.BlockMarkdownViewSet, basename="markdown-blocks")
router.register(r"media-blocks", views.BlockMEDIAViewSet, basename="media-blocks")
router.register(
    r"media-card-blocks", views.BlockMEDIACARDViewSet, basename="media-card-blocks"
)
router.register(
    r"container-blocks", views.BlockCONTAINERViewSet, basename="container-blocks"
)
router.register(
    r"carousel-blocks", views.BlockCAROUSELViewSet, basename="carousel-blocks"
)
router.register(r"button-blocks", views.BlockBUTTONViewSet, basename="button-blocks")
router.register(r"blocks", views.BlockViewSet, basename="blocks")
router.register(r"relationships", views.RelationShipsViewSet, basename="relationships")
router.register(r"composers", views.ComposerViewSet, basename="composers")
router.register(r"cards", views.BlockCARDViewSet, basename="cards")
router.register(r"card-group-blocks", views.BlockCARDGROUPViewSet, basename="card-groups")
router.register(r"hero-blocks", views.BlockHEROViewSet, basename="heros")
router.register(r"cta-blocks", views.BlockCTAViewSet, basename="cta-blocks")
router.register(r"marquee-blocks", views.BlockMarqueeViewSet, basename="marquee-blocks")
router.register(r"footer-link-blocks", views.BlockFOOTERLINKSViewSet, basename="footer-link-blocks")
router.register(r"navbar-blocks", views.BlockNAVBARViewSet, basename="navbar-blocks")
router.register(r"product-filter-blocks", views.BlockFilterProductViewSet, basename="product-filter-blocks")
router.register(r"post-filter-blocks", views.BlockFilterPostViewSet, basename="post-filter-blocks")
router.register(r"brand-filter-blocks", views.BlockFilterBrandViewSet, basename="brand-filter-blocks")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "page/<slug:slug>/",
        views.PageSlugView.as_view(),
        name="page-slug-detail",
    ),
    path("headers/", views.HeaderAPIView.as_view(), name="headers"),
    path("footers/", views.FooterAPIView.as_view(), name="footers"),
    path("landings/", views.LandingAPIView.as_view(), name="landings"),
    path("shop-pages/", views.ShopPageAPIView.as_view(), name="shop-pages"),
    path("blog-pages/", views.BlogPageAPIView.as_view(), name="blog-pages"),
]
