<template>
  <div class="app-wrapper">
    <div id="app">
      <div id="toolbar"></div>
      <div id="map" ref="map"></div>
    </div>
  </div>
</template>

<script>
  import L from 'leaflet'
  import axios from 'axios'
  import tinycolor from 'tinycolor2'

  export default {
    name: 'app',
    data () {
      return {
        map: null,
        roads: [],
        roadsLayer: null,
        marker: null,
        popup: null,
      }
    },
    watch: {
      roads () {
        if (this.map) {
          this.roadsLayer.clearLayers();
          this.roads.forEach(geoObject => {
            let k = 1 - (geoObject.properties.score - 2) / 3;
            let polyline = L.geoJSON(geoObject, {
              onEachFeature: this.onEachFeature.bind(this),
              style: {
                'color': tinycolor.mix('#07b500', '#ff0071', k * 100).toString(),
                'weight': 10,
                'opacity': 0.75
              }
            })
            polyline.addTo(this.roadsLayer)
          })
        }
      }
    },
    created () {
      axios.get('/api/road/').then(r => {
        this.roads = r.data.roads
      })
    },
    mounted () {
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
      onEachFeature (feature, layer) {
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
                rq_id: e.rq_id,
                video_id: feature.properties.video_id
              }
            }).then(r => {
              let address = `${Math.floor(r.data.position / 1000)}+${r.data.position % 1000}`
              self.popup.setContent(`
<h2>${feature.properties.road_title}</h2>
<h3>адрес: ${address}</h3>
<img src="${r.data.url}">
`);
            })

            self.map.openPopup(self.popup);
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
    flex-direction: column;
  }

  #toolbar {
    height: 50px;
    border-bottom: 1px solid silver;
  }

  #map {
    flex-grow: 1;
  }

  .leaflet-popup-content img {
    max-width: 100%;
  }
</style>
