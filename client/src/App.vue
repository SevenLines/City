<template>
  <div style="height: 100%">
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
                <div class="address">{{frameAddress}}</div> &mdash;
                <div class="road-title">{{frameRoadTitle}}</div>
              </h3>
              <img :src="frameUrl" alt="">
              <div style="padding-top: 0.5em">
                <strong>Оценка состояния дороги: {{frameScore}}</strong>
                <div><strong>Дефекты:</strong> {{frameDefects}}</div>
              </div>
            </div>
            <div v-show="!frameAddress" style="padding-top: 1em">
              Кликнете дорогу на карте, чтобы увидеть состояние дороги
            </div>
          </div>
          <div class="filter">
            <div class="header">Слои дефектов</div>

            <div class="filter-list">
              <div>
                <el-checkbox v-model="showQuality"></el-checkbox>
                Состояние покрытия (двигайте ползунок, выбрано от <strong>{{quality[0]}}</strong> до <strong>{{quality[1]}}</strong>)
              </div>

              <el-slider
                v-model="quality"
                :step="0.1"
                :min=1
                :max=5
                :disabled="loadingQuality"
                range
                show-stops>
              </el-slider>
              <div v-for="f in filters">
                <div v-if="f.id" class="filter-item">
                  <div class="sample" :style="{'background-color': f.color}"></div>
                  <filter-item class="checkbox" :data="f" @valueChanged="onValueChanged"/>
                </div>
                <div v-if="!f.id">
                  <hr>
                </div>
              </div>
              <div>
                <el-checkbox v-model="showBorder">Бордюры в неудов. состоянии</el-checkbox>
              </div>
              <div>
                <el-checkbox v-model="showBarrier">Огражения в неудов. состоянии</el-checkbox>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="loading-spinner" v-if="loading">
      <half-circle-spinner
        :animation-duration="1000"
        :size="60"
        color="#ff1d5e"
      />
      <div class="message">
        Обновляю данные
      </div>
    </div>
  </div>
</template>


<script>
  import L from 'leaflet'
  import axios from 'axios'
  import _ from 'lodash'
  import tinycolor from 'tinycolor2'
  import {HalfCircleSpinner} from 'epic-spinners'
  import FilterItem from './Filter.vue'

  export default {
    name: 'app',
    data() {
      return {
        loadingQuality: false,
        loadingBarriers: false,
        loadingDefects: false,
        map: null,
        roads: [],
        roads_list: {},
        roadsLayer: null,
        pointsLayer: null,
        pointsDefects: [],

        multilineDefectsLayer: null,
        multilineDefects: [],
        borderLayer: null,
        barrierLayer: null,

        marker: null,
        popup: null,
        frameRoadTitle: '',
        frameUrl: '',
        frameScore: '',
        frameDefects: '',
        frameAddress: '',
        quality: [2, 5],

        showQuality: true,
        showBorder: true,
        showBarrier: true,

        filterBorder: false,

        filters: [
          {id: '1', title: 'Разрушение а/б около канализационного люка', value: false, color: '#ff0017'},
          {id: '2', title: 'Выпирающий канализационный люк', value: false, color: '#ff8930'},
          {id: '7', title: 'Отсутствующий канализационный люк', value: false, color: '#ffb42a'},
          {id: '12', title: 'Продавленный канализационный люк', value: false, color: '#faff02'},
          {id: null},
          {
            id: '4',
            title: 'Разрушение ц/б плит на пересекаемых трамвайных (ж/д) путях',
            value: false,
            color: '#0069ff'
          },
          {id: '6', title: 'Разрушение а/б на пересекаемых трамвайных (ж/д) путях', value: false, color: '#2793bd'},
          {
            id: '10',
            title: 'Отклонение верха головки рельса трамвайных или железнодорожных путей, расположенных в пределах проезжей части, относительно покрытия более 2,0 см.',
            value: false,
            color: '#2fcbc8'
          },
          // {id: null},
          // {id: '6', title: 'Плохое состояние ограждений и бородюрного камня', value: false, color: '#cd00ff'},
        ]
      }
    },
    components: {
      'filter-item': FilterItem,
      HalfCircleSpinner
    },
    computed: {
      loading() {
        return this.loadingDefects || this.loadingQuality || this.loadingBarriers
      }
    },
    watch: {
      showQuality() {
        let self = this;
        if (this.showQuality) {
          this.roadsLayer.addTo(this.map)
        } else {
          this.roadsLayer.remove()
        }
        this.loadBarriers()
      },
      showBorder() {
        if (this.showBorder) {
          this.borderLayer.addTo(this.map)
        } else {
          this.borderLayer.remove()
        }
      },
      showBarrier() {
        if (this.showBarrier) {
          this.barrierLayer.addTo(this.map)
        } else {
          this.barrierLayer.remove()
        }
      },
      quality() {
        this.loadQuality()
      },
      roads() {
        let self = this;
        if (this.map) {
          this.roadsLayer.clearLayers();
          _.chunk(this.roads, 10).forEach(roads => {
            setTimeout(function () {
              roads.forEach(geoObject => {
                let k = 1 - (geoObject.properties.score - 2) / 3;
                let polyline = L.geoJSON(geoObject, {
                  onEachFeature: self.onEachFeature.bind(self),
                  style: {
                    'color': tinycolor.mix('#00e14b', '#ff0071', k * 100).toString(),
                    'weight': 10,
                    'opacity': 0.75
                  }
                });
                polyline.addTo(self.roadsLayer)
              })
            }, 10)
          });
          // this.reorder()
        }
      },
      multilineDefects() {
        let self = this;
        if (this.multilineDefects) {
          this.multilineDefectsLayer.clearLayers();
          _.chunk(self.multilineDefects, 10).forEach(multilineDefects => {
            setTimeout(function () {
              multilineDefects.forEach(geoObject => {
                let color = geoObject.properties.type === 'Бортовой камень' ? '#003aff' : '#ff0021';
                let layer = geoObject.properties.type === 'Бортовой камень' ? self.borderLayer : self.barrierLayer;
                let polyline = L.polyline(geoObject.geometry.coordinates.map(i => [i[1], i[0]]), {
                  'color': color,
                });

                polyline.addTo(layer)
              });
            }, 10);
          })
        }
      },
      pointsDefects() {
        if (this.map) {
          this.pointsLayer.clearLayers();
          this.pointsDefects.forEach(geoObject => {

            let defect_id = geoObject.properties.defects[0];
            let address = `${Math.floor(geoObject.properties.l / 1000)}+${geoObject.properties.l % 1000}`;
            let road_title = this.roads_list[geoObject.properties.road_id];
            let color = 'red';
            this.filters.some(i => {
              if (i.id == defect_id) {
                color = i.color
              }
            });

            let defectsVerbose = this.filters.map(i => {
              return {
                id: parseInt(i.id),
                title: i.title
              }
            }).filter(i => {
              return geoObject.properties.defects.indexOf(i.id) > -1
            }).map(i => i.title);

            let marker = L.circleMarker(
              [
                geoObject.geometry.coordinates[1],
                geoObject.geometry.coordinates[0],
              ], {
                radius: 5,
                color: 'white',
                fillColor: color,
                fillOpacity: 1,
                weight: 2
              }
            );
            marker.on('click', e => {
              this.popup.setContent(`<h3>${road_title} &mdash; ${address}</h3>` + defectsVerbose.join("<br>"));
              this.popup.setLatLng(e.latlng);
              this.popup.openOn(this.map)
            });
            marker.addTo(this.pointsLayer)
          });
        }
      }
    },
    created() {
      this.loadQuality();

    },

    mounted() {
      this.map = L.map(this.$refs.map, {
        renderer: L.canvas()
      }).setView([52.27, 104.3], 13);

      this.map.on('mouseover', e => {
        console.log(e);
      });

      L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
      }).addTo(this.map);

      this.popup = L.popup({
        minWidth: 300
      });

      this.marker = L.circleMarker([52.27, 104.3]);
      this.marker.addTo(this.map);

      this.roadsLayer = L.layerGroup();
      this.roadsLayer.addTo(this.map);

      this.pointsLayer = L.layerGroup();
      this.pointsLayer.addTo(this.map);

      this.multilineDefectsLayer = L.layerGroup();
      this.multilineDefectsLayer.addTo(this.map);

      this.borderLayer = L.layerGroup();
      this.borderLayer.addTo(this.map);
      this.barrierLayer = L.layerGroup();
      this.barrierLayer.addTo(this.map);
    },
    methods: {
      loadQuality: _.debounce(function () {
        this.loadingQuality = true;
        axios.get(`/api/road/${this.quality[0]}/${this.quality[1]}`).then(r => {
          this.roads = r.data.roads;
          this.roads_list = r.data.roads_list;
          this.loadingQuality = false;
          this.loadDefects();
          this.loadBarriers()
        })
      }, 300),
      loadDefects: _.debounce(function () {
        this.loadingDefects = true;
        axios.get('/api/point-defects/', {
          params: {
            filters: this.filters.filter(i => i.value).map(i => i.id)
          }
        }).then(r => {
          this.pointsDefects = r.data.defects;
          this.loadingDefects = false;
        })
      }, 600),
      loadBarriers: _.debounce(function () {
        this.loadingBarriers = true;
        axios.get('/api/multiline-defects/').then(r => {
          this.multilineDefects = r.data.lines;
          this.loadingBarriers = false;
        })
      }, 500),
      reorder() {
        this.multilineDefectsLayer.remove();
        this.multilineDefectsLayer.addTo(this.map);
        this.pointsLayer.remove();
        this.pointsLayer.addTo(this.map);
      },
      onValueChanged() {
        this.loadDefects()
      },
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


<style lang="scss" src="./app.scss">
</style>
