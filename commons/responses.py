from rest_framework.response import Response

class CustomeResponse(Response):
    @staticmethod
    def success(data=None, message="Success", status=200):
        response_data = { "status":"success", "message":message, "data":data, }
        return Response(response_data, status=status)

    @staticmethod
    def error(message="Error", status=400, data=None):
        response_data = { "status":"error", "message":message, "data":data, }
        return Response(response_data, status=status)