from flask import jsonify

# Global response format
class Response:
    @staticmethod
    def success(data=None, message="成功"):
        return jsonify({
            "code": 200,
            "message": message,
            "data": data
        })
    
    @staticmethod
    def error(code=500, message="失败", data=None):
        return jsonify({
            "code": code,
            "message": message,
            "data": data
        })
