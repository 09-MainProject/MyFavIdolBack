from django.conf import settings
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from . import oauth_views_old
from .oauth_views import (
    GoogleCallbackView,
    GoogleLoginRedirectView,
    KakaoCallbackView,
    KakaoLoginRedirectView,
    NaverCallbackView,
    NaverLoginRedirectView,
)
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutAPIView,
    PasswordCheckView,
    ProfileView,
    RegisterView,
    VerifyEmailView,
)

app_name = "user"

urlpatterns = [
    # 회원가입
    path("signup", RegisterView.as_view(), name="signup"),
    # 이메일 인증
    path("verify/email", VerifyEmailView.as_view(), name="verify_email"),
    # 비밀번호 확인
    path("check/password", PasswordCheckView.as_view(), name="password_check"),
    # 프로필
    path("profile", ProfileView.as_view(), name="profile"),
    # JWT 로그인, 로그아웃, 리프레시
    path("token/login", CustomTokenObtainPairView.as_view(), name="token_login"),
    path("token/logout", LogoutAPIView.as_view(), name="token_logout"),
    path("token/refresh", CustomTokenRefreshView.as_view(), name="token_refresh"),
    # path("token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # oauth naver
    path(
        "naver/login",
        NaverLoginRedirectView.as_view(),
        name="naver_login",
    ),
    path("naver/callback", NaverCallbackView.as_view(), name="naver_callback"),
    # oauth kakao
    path(
        "kakao/login",
        KakaoLoginRedirectView.as_view(),
        name="kakao_login",
    ),
    path("kakao/callback", KakaoCallbackView.as_view(), name="kakao_callback"),
    # oauth google
    path(
        "google/login",
        GoogleLoginRedirectView.as_view(),
        name="google_login",
    ),
    path("google/callback", GoogleCallbackView.as_view(), name="google_callback"),
]

# 개발 환경에서만 test용 OAuth URL 추가
if settings.ENV.get("DJANGO_ENV", "local") == "local":
    urlpatterns += [
        path(
            "naver/login-test",
            oauth_views_old.NaverLoginRedirectView.as_view(),
            name="naver_login_test",
        ),
        path(
            "naver/callback-test",
            oauth_views_old.NaverCallbackView.as_view(),
            name="naver_callback_test",
        ),
        path(
            "kakao/login-test",
            oauth_views_old.KakaoLoginRedirectView.as_view(),
            name="kakao_login_test",
        ),
        path(
            "kakao/callback-test",
            oauth_views_old.KakaoCallbackView.as_view(),
            name="kakao_callback_test",
        ),
        path(
            "google/login-test",
            oauth_views_old.GoogleLoginRedirectView.as_view(),
            name="google_login_test",
        ),
        path(
            "google/callback-test",
            oauth_views_old.GoogleCallbackView.as_view(),
            name="google_callback_test",
        ),
        path(
            "oauth/callback-test",
            oauth_views_old.oauth_callback_test_page,
            name="oauth-callback-test",
        ),
    ]
