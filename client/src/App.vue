<template>
  <div class="app-wrapper">
    <div id="app">
      <div id="map" ref="map"></div>
      <div id="toolbar">
        <div class="header">
          <img src="./assets/logo_2.png" alt="">
          <div>Иркутск &mdash; диагностика 2018</div>
        </div>
        <div class="info">
          <div v-show="frameAddress">
            <h3>
              <div class="address">{{frameAddress}}</div> &mdash; <div class="road-title">{{frameRoadTitle}}</div>
            </h3>
              <img :src="frameUrl" alt="">
            <div style="padding-top: 0.5em">
              <strong>Оценка состояния дороги: {{frameScore}}</strong>
              <div><strong>Дефекты:</strong> {{frameDefects}}</div>
            </div>
          </div>
          <div v-show="!frameAddress" style="padding-top: 1em">
            Кликнете дорогу на карте, чтобы увидеть сосотяние дороги
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import L from 'leaflet'
  import axios from 'axios'
  import tinycolor from 'tinycolor2'

  export default {
    name: 'app',
    data() {
      return {
        map: null,
        roads: [],
        roads_list: {},
        roadsLayer: null,
        marker: null,
        popup: null,
        frameRoadTitle: '',
        frameUrl: '',
        frameScore: '',
        frameDefects: '',
      }
    },
    watch: {
      roads() {
        if (this.map) {
          this.roadsLayer.clearLayers();
          this.roads.forEach(geoObject => {
            let k = 1 - (geoObject.properties.score - 2) / 3;
            let polyline = L.geoJSON(geoObject, {
              onEachFeature: this.onEachFeature.bind(this),
              style: {
                'color': tinycolor.mix('#00e14b', '#ff0071', k * 100).toString(),
                'weight': 10,
                'opacity': 0.75
              }
            })
            polyline.addTo(this.roadsLayer)
          })
        }
      }
    },
    created() {
      axios.get('/api/road/').then(r => {
        this.roads = r.data.roads;
        this.roads_list = r.data.roads_list;
      })
    },
    mounted() {
      this.map = L.map(this.$refs.map).setView([52.27, 104.3], 13)
      L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
      }).addTo(this.map);

      this.popup = L.popup({
        minWidth: 500
      });

      this.marker = L.circleMarker([52.27, 104.3]);
      this.marker.addTo(this.map);

      this.roadsLayer = L.layerGroup();
      this.roadsLayer.addTo(this.map)

    },
    methods: {
      onEachFeature(feature, layer) {
        let self = this;
        layer.on({
          hover(e) {
            self.marker.setLatLng(e.latlng);
          },
          click(e) {
            self.marker.setLatLng(e.latlng);

            self.popup.setLatLng(e.latlng);
            self.popup.setContent("загрузка...");

            axios.get('/api/nearest-frame', {
              params: {
                lat: e.latlng.lat,
                lng: e.latlng.lng,
                rq_id: feature.properties.rq_id,
                video_id: feature.properties.video_id
              }
            }).then(r => {
              let position = Math.abs(r.data.position);
              let address = `${Math.floor(position / 1000)}+${position % 1000}`;
              let road_title = self.roads_list[feature.properties.road_id];
              self.frameUrl = r.data.url;
              self.frameRoadTitle = road_title;
              self.frameDefects = r.data.defects;
              self.frameScore = r.data.score;
              self.frameAddress = address
            });
          }
        })
      }
    }
  }
</script>

<style lang="scss">
  @import "~leaflet/dist/leaflet.css";

  body, html {
    height: 100%;
    padding: 0;
    margin: 0;
  }

  .app-wrapper {
    display: flex;
    height: 100%;
  }

  #app {
    width: 100%;
    display: flex;
    /*flex-direction: column;*/
  }

  #toolbar {
    .header {
      display: flex;
      justify-content: flex-start;
      align-items: center;
      padding: 0.5em;
      background: #5dc3f4;
      box-shadow: 0 0 32px #55abd9 inset, 0 0 2px #97a6c0;
      font-size: 2em;
      img {
        padding-right: 0.5em;
      }
      border-bottom: 1px solid #cccccc;
    }
    .info {
      overflow: hidden;
      padding: 1em;
      .address {
        $color: #0046ff;
        display: inline-block;
        background-color: $color;
        padding: 0.25em 0.5em;
        color: white;
        border-radius: 0.5em;
        box-shadow: 0 0 0 2px white, 0 0 0 4px $color;
        margin-right: 4px;
      }
      .road-title {
        display: inline-block;
        max-width: 400px;
        white-space: nowrap;
        text-overflow: ellipsis;
      }
      img {
        max-width: 100%;
        box-shadow: 0 0 8px silver;
      }

    }
    flex-basis: 600px;
    box-shadow: 0 0 8px silver;

    h2, h3 {
      padding: 0;
      margin: 0;
    }
    h3 {
      margin-bottom: 1em;
    }
    border-bottom: 1px solid silver;
  }

  #map {
    flex-grow: 1;
  }

  .leaflet-popup-content img {

  }
</style>
