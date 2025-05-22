# views.py

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from utils.responses import idol_schedule as S

from .models import Idol, Schedule
from .serializers import ScheduleSerializer


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsIdolManagerOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        return (
            [permissions.AllowAny()] if self.request.method == "GET" else [IsManager()]
        )

    def get_queryset(self):
        idol_id = self.kwargs["idol_id"]
        filters = Q(idol_id=idol_id)

        # query_map을 통해 QueryParam 기반 동적 필터링 수행
        # 각 필드에 대해 해당 조건이 있을 경우 Q 객체에 추가
        query_map = {
            "title": "title__icontains",
            "description": "description__icontains",
            "location": "location__icontains",
            "start_date": "start_date__gte",
            "end_date": "end_date__lte",
        }

        for param, lookup in query_map.items():
            if value := self.request.query_params.get(param):
                filters &= Q(**{lookup: value})

        return Schedule.objects.select_related("idol", "user").filter(filters)

    @swagger_auto_schema(
        operation_summary="아이돌 일정 목록 조회",
        tags=["아이돌 일정"],
        manual_parameters=[
            openapi.Parameter(
                p, openapi.IN_QUERY, description=f"{p} 검색", type=openapi.TYPE_STRING
            )
            for p in ["title", "description", "location"]
        ]
        + [
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="시작일 이후",
                type=openapi.TYPE_STRING,
                format="date",
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="종료일 이전",
                type=openapi.TYPE_STRING,
                format="date",
            ),
        ],
        responses={200: ScheduleSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        message = S.SCHEDULE_LIST_SUCCESS if queryset else S.SCHEDULE_LIST_EMPTY
        return Response(
            {
                "code": message["code"],
                "message": message["message"],
                "data": self.get_serializer(queryset, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_summary="아이돌 일정 등록",
        tags=["아이돌 일정"],
        request_body=ScheduleSerializer,
        responses={201: ScheduleSerializer()},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "code": S.SCHEDULE_CREATE_FAIL["code"],
                    "message": S.SCHEDULE_CREATE_FAIL["message"],
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_create(serializer)
        return Response(
            {
                "code": S.SCHEDULE_CREATE_SUCCESS["code"],
                "message": S.SCHEDULE_CREATE_SUCCESS["message"],
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        idol_id = self.kwargs["idol_id"]
        idol = Idol.objects.filter(id=idol_id).first()

        if not idol:
            raise PermissionDenied(S.SCHEDULE_IDOL_NOT_FOUND["message"])

        # 요청 사용자가 해당 아이돌의 매니저인지 권한 확인
        if self.request.user not in idol.managers.all():
            raise PermissionDenied(S.SCHEDULE_PERMISSION_DENIED["message"])

        serializer.save(user=self.request.user, idol=idol)


class ScheduleRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        return (
            [permissions.AllowAny()]
            if self.request.method == "GET"
            else [IsIdolManagerOrOwner()]
        )

    def get_queryset(self):
        # swagger 문서 생성용 가짜 요청 처리 (문서화 시 필요)
        if getattr(self, "swagger_fake_view", False):
            return Schedule.objects.none()
        return Schedule.objects.select_related("idol", "user").filter(
            idol_id=self.kwargs["idol_id"]
        )

    @swagger_auto_schema(
        operation_summary="아이돌 일정 상세 조회",
        tags=["아이돌 일정"],
        responses={200: ScheduleSerializer},
    )
    def get(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return Response(
                {
                    "code": S.SCHEDULE_RETRIEVE_SUCCESS["code"],
                    "message": S.SCHEDULE_RETRIEVE_SUCCESS["message"],
                    "data": {"schedule_view": self.get_serializer(instance).data},
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "code": S.SCHEDULE_NOT_FOUND["code"],
                    "message": S.SCHEDULE_NOT_FOUND["message"],
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    @swagger_auto_schema(
        operation_summary="아이돌 일정 수정",
        tags=["아이돌 일정"],
        request_body=ScheduleSerializer,
        responses={200: ScheduleSerializer},
    )
    def patch(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(
                    {
                        "code": S.SCHEDULE_UPDATE_SUCCESS["code"],
                        "message": S.SCHEDULE_UPDATE_SUCCESS["message"],
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "code": S.SCHEDULE_UPDATE_FAIL["code"],
                    "message": S.SCHEDULE_UPDATE_FAIL["message"],
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied:
            return Response(
                {
                    "code": S.SCHEDULE_UPDATE_PERMISSION_DENIED["code"],
                    "message": S.SCHEDULE_UPDATE_PERMISSION_DENIED["message"],
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(
        operation_summary="아이돌 일정 삭제",
        tags=["아이돌 일정"],
        responses={204: "삭제 성공"},
    )
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    "code": S.SCHEDULE_DELETE_SUCCESS["code"],
                    "message": S.SCHEDULE_DELETE_SUCCESS["message"],
                    "data": {"schedule_id": instance.id},
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except PermissionDenied:
            return Response(
                {
                    "code": S.SCHEDULE_DELETE_PERMISSION_DENIED["code"],
                    "message": S.SCHEDULE_DELETE_PERMISSION_DENIED["message"],
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    @swagger_auto_schema(auto_schema=None)
    def put(self, request, *args, **kwargs):
        # PUT은 허용하지 않음 (명시적으로 405 반환)
        return Response(
            {
                "code": "METHOD_NOT_ALLOWED",
                "message": "PUT 메서드는 지원되지 않습니다.",
                "data": None,
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
