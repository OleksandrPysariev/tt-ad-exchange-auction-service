from app.db.dao.common import CommonDAO
from app.db.models.bidder import Bidder
from app.models.bidder import BidderCreate, BidderUpdate


class BidderDAO(CommonDAO[Bidder, BidderCreate, BidderUpdate]):
    pass


bidder_dao = BidderDAO(Bidder)
