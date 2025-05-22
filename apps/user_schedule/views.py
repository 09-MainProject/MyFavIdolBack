from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.follow.models import Follow
from apps.idol_schedule.models import Schedule
from apps.idol_schedule.serializers import IdolScheduleSerializer
from utils.responses import user_schedule as R

from .models import UserSchedule
from .serializers import UserScheduleSerializer


# 일정 목록 조회 및 사용자 일정 생성
class UserScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = UserScheduleSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="내 일정 목록 조회 (팔로우한 아이돌 일정 포함)",
        tags=["사용자 일정"],
        responses={
            200: "사용자 일정 + 팔로우 아이돌 일정",
        },
    )
    def get(self, request, *args, **kwargs):
        user = request.user

        # 사용자 일정 조회
        user_schedules = self.get_queryset()
        user_schedule_data = self.get_serializer(user_schedules, many=True).data

        # 팔로우한 아이돌의 일정 조회
        followed_idol_ids = Follow.objects.filter(user=user).values_list(
            "idol_id", flat=True
        )
        idol_schedules = Schedule.objects.select_related("idol").filter(
            idol_id__in=followed_idol_ids
        )
        idol_schedule_data = IdolScheduleSerializer(idol_schedules, many=True).data

        return Response(
            {
                "code": R.SCHEDULE_LIST_SUCCESS["code"],
                "message": R.SCHEDULE_LIST_SUCCESS["message"],
                "data": {
                    "user_schedules": user_schedule_data,
                    "idol_schedules": idol_schedule_data,
                },
            },
            status=R.SCHEDULE_LIST_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 등록",
        tags=["사용자 일정"],
        request_body=UserScheduleSerializer,
        responses={
            201: UserScheduleSerializer(),
        },
    )
    def post(self, request, *args, **kwargs):
        # 사용자 일정 등록
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {
                "code": R.SCHEDULE_CREATE_SUCCESS["code"],
                "message": R.SCHEDULE_CREATE_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_CREATE_SUCCESS["status"],
        )


# 일정 상세 조회, 수정, 삭제
class UserScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "patch", "delete"]
    serializer_class = UserScheduleSerializer
    queryset = UserSchedule.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_object(self):
        # 요청 사용자의 소유 일정만 조회 가능
        try:
            obj = super().get_object()
        except UserSchedule.DoesNotExist:
            raise NotFound(R.SCHEDULE_NOT_FOUND["message"])

        if obj.user != self.request.user:
            raise PermissionDenied(R.SCHEDULE_NO_PERMISSION["message"])

        return obj

    @swagger_auto_schema(
        operation_summary="내 일정 상세 조회",
        tags=["사용자 일정"],
        responses={
            200: UserScheduleSerializer(),
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule)
        return Response(
            {
                "code": R.SCHEDULE_DETAIL_SUCCESS["code"],
                "message": R.SCHEDULE_DETAIL_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_DETAIL_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 수정",
        tags=["사용자 일정"],
        request_body=UserScheduleSerializer,
        responses={
            200: UserScheduleSerializer(),
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "code": R.SCHEDULE_UPDATE_SUCCESS["code"],
                "message": R.SCHEDULE_UPDATE_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_UPDATE_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 삭제",
        tags=["사용자 일정"],
        responses={
            204: "일정 삭제 성공",
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        schedule.delete()
        return Response(
            {
                "code": R.SCHEDULE_DELETE_SUCCESS["code"],
                "message": R.SCHEDULE_DELETE_SUCCESS["message"],
            },
            status=R.SCHEDULE_DELETE_SUCCESS["status"],
        )
