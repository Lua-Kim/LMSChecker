from PIL import Image
import os
import io

class ICOGenerator:
    RESOLUTIONS = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    
    @staticmethod
    def create_ico(image, selected_sizes, output_path):
        """
        선택된 해상도로 ICO 파일 생성
        """
        try:
            sizes = [(size, size) for size in selected_sizes if size <= image.size[0]] # 유효한 사이즈만 필터링
            
            # 1. 메모리 내에서 ICO 데이터 생성
            ico_buffer = io.BytesIO()
            image.save(ico_buffer, format='ICO', sizes=sizes)
            ico_data = ico_buffer.getvalue()
            
            # 2. 파일로 저장
            with open(output_path, 'wb') as f:
                f.write(ico_data)
            
            return True, f"ICO 생성 완료: {len(sizes)}개 해상도", ico_data
        except Exception as e:
            return False, f"ICO 생성 실패: {str(e)}", None
    
    @staticmethod
    def validate_resolutions(image_size, selected_sizes):
        """유효한 해상도만 필터링"""
        max_size = min(image_size)
        return [s for s in selected_sizes if s <= max_size]