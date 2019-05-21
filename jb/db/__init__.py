from sqlalchemy import DateTime, Integer, func, Column
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import List, Any, Dict
import logging
from flask_sqlalchemy import SQLAlchemy

log = logging.getLogger(__name__)
TSTZ = DateTime(timezone=True)


class BaseModel(object):
    id = Column(Integer, primary_key=True)
    created = Column(TSTZ, nullable=False, server_default=func.now())
    updated = Column(TSTZ, nullable=True, onupdate=func.now())
    deleted = Column(TSTZ, nullable=True)


db = SQLAlchemy(model_class=BaseModel)
Model = db.Model


# model mixin
class Upsertable():
    """Model mixin to provide postgres upsert capability."""

    @classmethod
    def upsert_row(cls,
                   row_class,
                   *,
                   session,
                   index_elements: List[str] = None,
                   constraint=None,
                   set_: Dict[str, Any],
                   should_return_result=True,
                   values: Dict[str, Any]):
        """Insert or update if index_elements match.

        N.B. does not commit.

        :set_: sets values if exists
        :values: are inserted if not exists
        :should_return_result: if false will not return object and will not do commit
        :returns: model fetched from DB.
        """
        # what do we detect conflict on?
        conflict = None
        if index_elements:
            conflict = {'index_elements': index_elements}
        elif constraint:
            conflict = {'constraint': constraint}
        else:
            raise Exception("constraint or index_elements must be specified")

        insert_query = pg_insert(row_class).on_conflict_do_update(
            **conflict,
            set_=set_,
        ).values(**values)
        res = session.execute(insert_query)
        if not should_return_result:
            return None
        assert res  # we always get a result if the query completes successfully right?
        session.commit()
        id = res.inserted_primary_key[0]
        result = session.query(row_class).get(id)
        assert result
        return result
