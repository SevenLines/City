<template>
    <el-checkbox v-model="data.value">{{data.title}}</el-checkbox>
</template>

<script>
  export default {
    props: ['data'],
    name: 'FilterItem',
    watch: {
      data: {
        deep: true,
        handler() {
          this.$emit("valueChanged")
        }
      }
    }
  }
</script>

<style scoped>

</style>
