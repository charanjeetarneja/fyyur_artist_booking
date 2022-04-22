#----------------------------------------------------------------------------#
# Import the libraries
#----------------------------------------------------------------------------#
from distutils import errors
from sys import exc_info
import dateutil.parser
import json
import babel
from flask_moment import Moment
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from forms import *
from sqlalchemy_utils import create_database, database_exists
import logging
from logging import Formatter, FileHandler
import config
from models import db, Artist, Venue, Show
import traceback
from flask_migrate import Migrate
from sqlalchemy.orm.exc import NoResultFound

#----------------------------------------------------------------------------#
# Application config Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  print(value)
  date = dateutil.parser.parse(value,ignoretz=True)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')

#----------------------------------------------------------------------------#
# Venues : Get/Search
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
    unique_city_states = Venue.query.distinct(Venue.city, Venue.state).all()
    data = [uniq_st.filter_city_state for uniq_st in unique_city_states]
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', None)
    venues = Venue.query.filter(
        Venue.name.ilike("%{}%".format(search_term))).all()
    venue_count = len(venues)
    response = {
        "count": venue_count,
        "data": [v.srlz for v in venues]
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venues = Venue.query.filter(Venue.id == venue_id).one_or_none()
    if venues is None:
        abort(404)
    data = venues.srlz_shows_details
    return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Venues: Create a Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    ven_form = VenueForm()
    return render_template('forms/new_venue.html', form=ven_form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    ven_form = VenueForm(request.form)
    if ven_form.validate():
        try:
            new_venue = Venue(
                name=ven_form.name.data,
                state=ven_form.state.data,
                phone=ven_form.phone.data,
                facebook_link=ven_form.facebook_link.data,
                website=ven_form.website.data,
                genres=','.join(ven_form.genres.data),
                address=ven_form.address.data,
                city=ven_form.city.data,
                image_link=ven_form.image_link.data,
                seeking_talent = ven_form.seeking_talent.data,
                seeking_description = ven_form.seeking_description.data)
            new_venue.add()
            # Successful insert into Database - notify on UI
            flash('Venue ' +
                request.form['name'] +
                ' was successfully onboarded.'+str(type(ven_form.genres.data)))
        except Exception as e:
            flash('Venue ' + request.form['name'] +  ' could not be onboarded. There was an error, please try again. ' + str(e))
            traceback.print_exc()
    else:
        for field,err_msgs in ven_form.errors.items():
            flash('The field ' + field +' has following error messages: ' + ','.join(err_msgs))
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venue : Edit an Venue
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    ven_update = Venue.query.filter(Venue.id == venue_id).one_or_none()
    if ven_update is None: 
        abort(404)

    ven = ven_update.srlz
    ven_form = VenueForm(data=ven)

    return render_template('forms/edit_venue.html', form=ven_form, venue=ven)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):  
    ven_form = VenueForm(request.form)
    if ven_form.validate():
        try:
            ven = Venue.query.filter(Venue.id==venue_id).one()
            ven.name = ven_form.name.data
            ven.city = ven_form.city.data
            ven.state = ven_form.state.data
            ven.phone = ven_form.phone.data
            ven.facebook_link = ven_form.facebook_link.data
            ven.image_link = ven_form.image_link.data
            ven.website = ven_form.website.data
            ven.address = ven_form.address.data
            ven.genres = ','.join(ven_form.genres.data)
            ven.seeking_talent=ven_form.seeking_talent.data
            ven.seeking_description = ven_form.seeking_description.data
            db.session.commit()
            # Successful insert into Database - notify on UI
            flash('Venue ' + request.form['name'] + ' was successfully edited.')
        except Exception as e:
            flash('Venue ' + request.form['name'] + ' could not be edited.There was an error, please try again.' + str(e))
    else:
        for field,err_msgs in ven_form.errors.items():
            flash('The field ' + field +' has following error messages: ' + ','.join(err_msgs))
    return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Venues: Delete a Venue
#  ----------------------------------------------------------------

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        ven = Venue.query.filter(Venue.id == venue_id).delete()
        try:
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
        flash('Venue '+ ven[0]['name'] +'has been deleted.')
    except NoResultFound:
        abort(404)
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Artists : Get/Search
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
    art = Artist.query.all()
    data = [a.srlz_shows_details for a in art]
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    srch_trm = request.form.get('search_term', None)
    art = Artist.query.filter(Artist.name.ilike("%{}%".format(srch_trm))).all()
    art_cnt = len(art)
    response = {
        "count": art_cnt,
        "data": [a.srlz for a in art]
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    art = Artist.query.filter(Artist.id == artist_id).one_or_none()

    if art is None:
        abort(404)

    art_data = art.srlz_shows_details

    return render_template('pages/show_artist.html', artist=art_data)

#  ----------------------------------------------------------------
#  Artists : Create an Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    art_form = ArtistForm()
    return render_template('forms/new_artist.html', form=art_form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    art_form = ArtistForm(request.form)
    if art_form.validate():
        try:
            new_artist = Artist(
                name=art_form.name.data,
                phone=art_form.phone.data,
                facebook_link=art_form.facebook_link.data,
                image_link=art_form.image_link.data,
                website=art_form.website.data,
                genres=','.join(art_form.genres.data),
                address=art_form.address.data,
                city=art_form.city.data,
                state=art_form.state.data,
                seeking_venue=art_form.seeking_venue.data,
                seeking_description=art_form.seeking_description.data)
            new_artist.add()
            # Successful insert into Database - notify on UI
            flash('Artist ' + request.form['name'] + ' was successfully onboarded.')
        except Exception as e:
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be onboarded. There was an error, please try again. ' + str(e))
    else:
        for field,err_msgs in art_form.errors.items():
            flash('The field ' + field +' has following error messages: ' + ','.join(err_msgs))
    return render_template('pages/home.html')
    
#  ----------------------------------------------------------------
#  Artist : Edit an Artist
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

    art_update = Artist.query.filter(Artist.id == artist_id).one_or_none()
    if art_update is None:    
        abort(404)
    else:    
        art = art_update.srlz
        art_form = ArtistForm(data=art)
    return render_template('forms/edit_artist.html', form=art_form, artist=art)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    art_form = ArtistForm(request.form)
    if art_form.validate():
        try:
            art_update = Artist.query.filter_by(id=artist_id).one()
            art_update.artist.name = art_form.name.data
            art_update.state = art_form.state.data
            art_update.phone = art_form.phone.data
            art_update.facebook_link = art_form.facebook_link.data
            art_update.image_link = art_form.image_link.data
            art_update.website = art_form.website.data
            art_update.genres = ','.join(art_form.genres.data)
            art_update.city = art_form.city.data
            art_update.seeking_venue=art_form.seeking_venue.data
            art_update.seeking_description=art_form.seeking_description.data
            db.session.commit()
            # Successful insert into Database - notify on UI
            flash('Artist ' + request.form['name'] + ' was successfully edited.')
        except Exception as e:
            flash('Artist ' + request.form['name'] + ' could not be edited. An error occurred.' + str(e))
    else:
        for field,err_msgs in art_form.errors.items():
            flash('The field ' + field +' has following error messages: ' + ','.join(err_msgs))
    return redirect(url_for('show_artist', artist_id=artist_id))

#  ----------------------------------------------------------------
#  Shows : Get
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shs = Show.query.all()
    shows_data = [s.srlz_artist_venue for s in shs]
    return render_template('pages/shows.html', shows=shows_data)

#  ----------------------------------------------------------------
#  Shows : Create a show
#  ----------------------------------------------------------------

@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    show_form = ShowForm(request.form)
    try:
        show = Show(
            artist_id=show_form.artist_id.data,
            venue_id=show_form.venue_id.data,
            start_time=show_form.start_time.data
        )
        show.add()
        # Successful insert into Database - notify on UI
        flash('Show was successfully onboarded.')
    except Exception as e:
        flash('Show could not be onboarded. An error occured, please try again.'+str(e))

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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
