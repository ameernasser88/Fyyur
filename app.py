# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form

from forms import *
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy.orm import backref
import os

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#
app = Flask(__name__)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

venue_genres = db.Table('venue_genres', db.Column('venue_id', db.ForeignKey('Venue.id'), primary_key=True)
                        , db.Column('genre_id', db.ForeignKey('Genre.id'), primary_key=True))

artist_genres = db.Table('artist_genres', db.Column('artist_id', db.ForeignKey('Artist.id'), primary_key=True)
                         , db.Column('genre_id', db.ForeignKey('Genre.id'), primary_key=True))


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    seeking_talent = db.Column(db.Boolean(), default=False, nullable=True)
    seeking_description = db.Column(db.String(500), nullable=True)
    genres = db.relationship('Genre', secondary=venue_genres, backref=db.backref('venues', lazy=True))

    def __repr__(self):
        return self.name




class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=True)
    image_link = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(120), nullable=True)
    seeking_venue = db.Column(db.Boolean(), default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    genres = db.relationship('Genre', secondary=artist_genres, backref=db.backref('artists', lazy=True))

    def __repr__(self):
        return self.name


class Genre(db.Model):
    __tablename__ = 'Genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return self.name


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)




# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = value
    if format == 'full':
        format = "%A %B, %d, %Y at %I:%M%p"
    elif format == 'medium':
        format = "%a %b, %d, %y %I:%M%p"
    return date.strftime(format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#
def model_search(form, model):
    search_term = form.get('search_term', '')
    search_pattern = "%" + search_term + "%"
    if model.lower() == 'venue':
        search_query = db.session.query(Venue).filter(Venue.name.ilike(search_pattern))
    else:
        search_query = db.session.query(Artist).filter(Artist.name.ilike(search_pattern))
    results = search_query.all()
    response = {}
    response['count'] = search_query.count()
    response['data'] = results
    return response


@app.route('/')
def index():
    recently_added_venues = Venue.query.order_by(Venue.id.desc()).limit(6)
    recently_added_artists = Artist.query.order_by(Artist.id.desc()).limit(6)
    return render_template('pages/home.html' , venues=recently_added_venues , artists=recently_added_artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    states_query = db.session.query(Venue.state.distinct().label("state")).order_by(Venue.state)
    states = [venue.state for venue in states_query.all()]
    venues = Venue.query.order_by(Venue.city).all()

    return render_template('pages/venues.html', states=states, venues=venues)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    response = model_search(form=request.form, model='Venue')
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term'))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_query = Venue.query.get(venue_id)
    if not venue_query:
        abort(404)

    venue = {}

    venue['id'] = venue_query.id
    venue['name'] = venue_query.name
    venue['city'] = venue_query.city
    venue['state'] = venue_query.state
    venue['address'] = venue_query.address
    venue['phone'] = venue_query.phone
    venue['image_link'] = venue_query.image_link
    venue['facebook_link'] = venue_query.facebook_link
    venue['website'] = venue_query.website
    venue['seeking_talent'] = venue_query.seeking_talent
    venue['seeking_description'] = venue_query.seeking_description
    venue['genres'] = venue_query.genres

    current_time = datetime.utcnow()

    upcoming_shows_query = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time>=current_time).order_by(Show.start_time)
    venue['upcoming_shows_count'] = upcoming_shows_query.count()
    venue['upcoming_shows'] = []
    for show in upcoming_shows_query.all():
        venue['upcoming_shows'].append({ "artist_id":show.artist_id
                                        ,"artist_image_link":Artist.query.get(show.artist_id).image_link
                                        ,"artist_name":Artist.query.get(show.artist_id).name
                                        ,"start_time":show.start_time
                                        })

    past_shows_query = Show.query.filter_by(venue_id=venue_id).filter(Show.start_time < current_time).order_by(Show.start_time)
    venue['past_shows_count'] = past_shows_query.count()
    venue['past_shows'] = []
    for show in past_shows_query.all():
        venue['past_shows'].append({ "artist_id":show.artist_id
                                        ,"artist_image_link":Artist.query.get(show.artist_id).image_link
                                        ,"artist_name":Artist.query.get(show.artist_id).name
                                        , "start_time": show.start_time
                                        })
    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    genres = Genre.query.all()
    count = Genre.query.count()
    if count == 0:
        genres_list = ['Alternative', 'Blues', 'Classical', 'Country', 'Electronic', 'Folk', 'Funk', 'Hip-Hop',
                       'Heavy Metal', 'Instrumental', 'Jazz', 'Musical Theatre', 'Pop', 'Punk', 'R&B', 'Reggae',
                       'Rock n Roll', 'Soul', 'Other']
        for genre in genres_list:
            temp = Genre(name=genre)
            db.session.add(temp)
        db.session.commit()
        genres = Genre.query.all()
        count = Genre.query.count()

    list_of_genres = []
    for i in range(0, count):
        list_of_genres.append((genres[i].id, genres[i].name))
    form.genres.choices = list_of_genres

    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        form = VenueForm(request.form)
        new_venue = Venue(name=form.data['name']
                          , city=form.data['city']
                          , state=form.data['state']
                          , address=form.data['address']
                          , facebook_link=form.data['facebook_link'] if form.data['facebook_link'] != '' else None
                          , phone=form.data['phone'] if form.data['phone'] != '' else None
                          , image_link=form.data['image_link'] if form.data['image_link'] != '' else None
                          , website=form.data['website'] if form.data['website'] != '' else None
                          , seeking_talent=form.data['seeking_talent']
                          , seeking_description=form.data['seeking_description'] if form.data['seeking_description'] != '' else None
                          )
        genres = []
        for genre_id in form.data['genres']:
            genres.append(Genre.query.get(genre_id))

        new_venue.genres = genres
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        shows = Show.query.filter_by(venue_id=venue_id)
        for show in shows:
            db.session.delete(show)
        db.session.delete(venue)
        db.session.commit()
        # on successful db delete, flash success
        flash('Venue ' + venue.name + ' was successfully deleted!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db delete, flash an error instead.
        flash('An error occurred. Artist ' + venue.name + ' could not be deleted')
    finally: 
        db.session.close()
    return render_template('pages/home.html')



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    artists = Artist.query.order_by(Artist.name).all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    response = model_search(form=request.form, model='Artist')
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_query = Artist.query.get(artist_id)
    if not artist_query:
        abort(404)

    artist = {}

    artist['id'] = artist_query.id
    artist['name'] = artist_query.name
    artist['city'] = artist_query.city
    artist['state'] = artist_query.state
    artist['phone'] = artist_query.phone
    artist['image_link'] = artist_query.image_link
    artist['facebook_link'] = artist_query.facebook_link
    artist['website'] = artist_query.website
    artist['seeking_venue'] = artist_query.seeking_venue
    artist['seeking_description'] = artist_query.seeking_description
    artist['genres'] = artist_query.genres

    current_time = datetime.utcnow()

    upcoming_shows_query = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time >= current_time).order_by(Show.start_time)
    artist['upcoming_shows_count'] = upcoming_shows_query.count()
    artist['upcoming_shows'] = []
    for show in upcoming_shows_query.all():
        artist['upcoming_shows'].append({"venue_id": show.venue_id
                                           , "venue_image_link": Venue.query.get(show.venue_id).image_link
                                           , "venue_name": Venue.query.get(show.venue_id).name
                                           , "start_time": show.start_time
                                        })

    past_shows_query = Show.query.filter_by(artist_id=artist_id).filter(Show.start_time < current_time).order_by(Show.start_time)
    artist['past_shows_count'] = past_shows_query.count()
    artist['past_shows'] = []
    for show in past_shows_query.all():
        artist['past_shows'].append({"venue_id": show.venue_id
                                           , "venue_image_link": Venue.query.get(show.venue_id).image_link
                                           , "venue_name": Venue.query.get(show.venue_id).name
                                           , "start_time": show.start_time
                                    })
    return render_template('pages/show_artist.html', artist=artist)

@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        shows = Show.query.filter_by(artist_id=artist_id)
        for show in shows:
            db.session.delete(show)
        db.session.delete(artist)
        db.session.commit()
        # on successful db delete, flash success
        flash('Artist ' + artist.name + ' was successfully deleted!')
    except:
        db.session.rollback()
        # TODO: on unsuccessful db delete, flash an error instead.
        flash('An error occurred. Artist ' + artist.name + ' could not be deleted')
    finally:
        db.session.close()
    return render_template('pages/home.html')
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        abort(404)
    form = ArtistForm(obj=artist)
    genres = Genre.query.all()
    count = Genre.query.count()
    list_of_genres = []
    for i in range(0, count):
        list_of_genres.append((genres[i].id, genres[i].name))
    form.genres.choices = list_of_genres

    artist_genres_query = Genre.query.join(artist_genres).join(Artist).filter(
        artist_genres.c.artist_id == artist_id).all()
    selected_genres = []
    for artist_genre in artist_genres_query:
        selected_genres.append(str(artist_genre.id))
    form.genres.data = selected_genres

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    try:
        form = ArtistForm(request.form)
        edited_artist = Artist.query.get(artist_id)
        artist_old_name = edited_artist.name
        edited_artist.name = form.data['name']
        edited_artist.city = form.data['city']
        edited_artist.state = form.data['state']
        edited_artist.facebook_link = form.data['facebook_link']
        edited_artist.phone = form.data['phone']
        edited_artist.image_link = form.data['image_link']
        edited_artist.website = form.data['website']
        edited_artist.seeking_venue = form.data['seeking_venue']
        edited_artist.seeking_description = form.data['seeking_description']
        genres = []
        for genre_id in form.data['genres']:
            genres.append(Genre.query.get(genre_id))

        edited_artist.genres = genres
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist' + request.form['name'] + ' was successfully edited!')

    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + artist_old_name + ' could not be edited.')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        abort(404)
    form = VenueForm(obj=venue)
    genres = Genre.query.all()
    count = Genre.query.count()
    list_of_genres = []
    for i in range(0, count):
        list_of_genres.append((genres[i].id, genres[i].name))
    form.genres.choices = list_of_genres

    venue_genres_query = Genre.query.join(venue_genres).join(Venue).filter(venue_genres.c.venue_id == venue_id).all()
    selected_genres = []
    for venue_genre in venue_genres_query:
        selected_genres.append(str(venue_genre.id))
    form.genres.data = selected_genres


    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    try:
        form = VenueForm(request.form)

        edited_venue = Venue.query.get(venue_id)
        venue_old_name = edited_venue.name
        edited_venue.name = form.data['name']
        edited_venue.city = form.data['city']
        edited_venue.state = form.data['state']
        edited_venue.address = form.data['address']
        edited_venue.facebook_link = form.data['facebook_link']
        edited_venue.phone = form.data['phone']
        edited_venue.image_link = form.data['image_link']
        edited_venue.website = form.data['website']
        edited_venue.seeking_talent = form.data['seeking_talent']
        edited_venue.seeking_description = form.data['seeking_description']
        genres = []
        for genre_id in form.data['genres']:
            genres.append(Genre.query.get(genre_id))

        edited_venue.genres = genres
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue' + request.form['name'] + ' was successfully edited!')

    except:

        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + venue_old_name + ' could not be edited.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    genres = Genre.query.all()
    count = Genre.query.count()
    if count == 0:
        genres_list = ['Alternative', 'Blues', 'Classical', 'Country', 'Electronic', 'Folk', 'Funk', 'Hip-Hop',
                       'Heavy Metal', 'Instrumental', 'Jazz', 'Musical Theatre', 'Pop', 'Punk', 'R&B', 'Reggae',
                       'Rock n Roll', 'Soul', 'Other']
        for genre in genres_list:
            temp = Genre(name=genre)
            db.session.add(temp)
        db.session.commit()
        genres = Genre.query.all()
        count = Genre.query.count()

    list_of_genres = []
    for i in range(0, count):
        list_of_genres.append((genres[i].id, genres[i].name))
    form.genres.choices = list_of_genres
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        form = ArtistForm(request.form)
        new_artist = Artist(  name=form.data['name']
                            , city=form.data['city']
                            , state=form.data['state']
                            , facebook_link=form.data['facebook_link'] if form.data['facebook_link'] != '' else None
                            , phone=form.data['phone'] if form.data['phone'] != '' else None
                            , image_link=form.data['image_link'] if form.data['image_link'] != '' else None
                            , website=form.data['website'] if form.data['website'] != '' else None
                            , seeking_venue=form.data['seeking_venue']
                            , seeking_description=form.data['seeking_description'] if form.data['seeking_description'] != '' else None
                            )
        genres = []
        for genre_id in form.data['genres']:
            genres.append(Genre.query.get(genre_id))

        new_artist.genres = genres
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.order_by('start_time').all()
    data = []
    count = 0
    for show in shows:
        data.append({"venue_id": show.venue_id,
                     "venue_name": Venue.query.get(show.venue_id).name,
                     "artist_id": show.artist_id,
                     "artist_name": Artist.query.get(show.artist_id).name,
                     "artist_image_link": Artist.query.get(show.artist_id).image_link,
                     "start_time": show.start_time
                     })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        form = ShowForm(request.form)
        new_show = Show(artist_id=form.data['artist_id'], venue_id=form.data['venue_id'],
                        start_time=form.data['start_time'])
        db.session.add(new_show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        error = True
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
