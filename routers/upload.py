from fastapi import APIRouter, UploadFile
from deps import CurrentUserDep
from photos import save_photo
from schemas import UploadOut


router = APIRouter(prefix='/api/uploads', tags=['upload'])


@router.post('', response_model=UploadOut, status_code=201)
def upload(photo: UploadFile, user: CurrentUserDep):
    # return save_photo(photo)
    return {'image_url': save_photo(photo)}