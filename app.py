# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

api = Api(app)
api.app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 4}
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


class DirectorSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


movie_schema = MovieSchema(many=True)


@movie_ns.route('/')
class MoviesView(Resource):
    """Вьюшка вывода всех фильмов просто так и по ID режиссера или жанра"""
    def get(self):
        all_movies = db.session.query(Movie).all()
        director_id = request.args.get('director_id')
        genre_id = request.args.get('genre_id')

        if director_id:
            all_movies = db.session.query(Movie).filter(Movie.director_id == director_id)

        if genre_id:
            all_movies = db.session.query(Movie).filter(Movie.genre_id == genre_id)

        if director_id and genre_id:
            all_movies = db.session.query(Movie).filter(Movie.genre_id == genre_id, Movie.director_id == director_id)

        return movie_schema.dump(all_movies), 200

    def post(self):
        req_json = request.json
        new_movie = Movie(**req_json)
        with db.session.begin():
            db.session.add(new_movie)
        return "", 201


@movie_ns.route('/<int:mid>')
class MovieView(Resource):
    """Вьюшка вывода одного фильма по ID"""
    def get(self, mid: int):
        try:
            movie = db.session.query(Movie).filter(Movie.id == mid)
            return movie_schema.dump(movie), 200
        except Exception as e:
            return str(e), 404


# Альтернативный вариант с URL "/directors/?director_id=":
@director_ns.route('/')
class DirectorView(Resource):
    """Вьюшка вывода фильма по ID директора"""
    def get(self):
        try:
            director = request.args.get("director_id", type=int)
            if director:
                movies_by_director = db.session.query(Movie.id,
                                                      Movie.title,
                                                      Movie.description,
                                                      Movie.trailer,
                                                      Movie.year,
                                                      Movie.rating,
                                                      Genre.name,
                                                      Director.name
                                                      ).filter(Movie.director_id == director)\
                    .join(Movie.genre).join(Movie.director).all()
                return movie_schema.dump(movies_by_director), 200
        except Exception as e:
            return str(e), 404


# Альтернативный вариант с URL "/genres/?genre_id=":
@genre_ns.route('/')
class GenreView(Resource):
    """Вьюшка вывода фильмов по ID жанра"""
    def get(self):
        try:
            genre = request.args.get("genre_id", type=int)
            if genre:
                movies_by_genre = db.session.query(Movie.id,
                                                   Movie.title,
                                                   Movie.description,
                                                   Movie.trailer,
                                                   Movie.year,
                                                   Movie.rating,
                                                   Genre.name,
                                                   Director.name
                                                   ).filter(Movie.genre_id == genre)\
                    .join(Movie.director).join(Movie.genre).all()
                return movie_schema.dump(movies_by_genre), 200
        except Exception as e:
            return str(e), 404


if __name__ == '__main__':
    app.run(debug=True)
