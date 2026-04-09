@router.delete("/{candidate_id}", status_code=http_status.HTTP_204_NO_CONTENT, summary="Delete candidate")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_candidate(db, candidate_id)
    except crud.CandidateNotFoundError as exc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


# ✅ ADD HERE
@router.get("/test")
def test_endpoint():
    return {"message": "API detection working"}