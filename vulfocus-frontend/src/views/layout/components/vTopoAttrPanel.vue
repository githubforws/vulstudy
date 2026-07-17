<!--
 * @Author: caojing
 * @Date: 2018-11-21 09:31:49
 * @LastEditors: caojing
 * @LastEditTime: 2018-11-23 14:43:14
 -->
<template>
  <div id="topoAttrWrap" :class="{active:isTopoAttrShow}">
    <h3 id="topoAttrHeader">属性设置框</h3>
    <div class="noAttrTip" v-if="JSON.stringify(nodeData) ==='{}'">
      未选择任何节点属性
    </div>
    <div v-show="isContainer">
      <el-form ref="containerForm" :model="image" label-width="80px">
        <el-form-item label="漏洞名称">
          <el-autocomplete v-model="searchImageName" style="width: 100%" size="small" placeholder="镜像名称"
                           :fetch-suggestions="querySearchImageAsync" @select="handleImageSelect"></el-autocomplete>
        </el-form-item>
        <el-form-item label="漏洞镜像">
          <el-input size="small" v-model="image.name" disabled></el-input>
        </el-form-item>
        <el-form-item label="漏洞描述">
          <el-input type="textarea" v-model="image.desc" size="small" disabled></el-input>
        </el-form-item>
        <el-form-item label="是否开放">
          <el-switch v-model="image.open"></el-switch>
        </el-form-item>
        <el-form-item label="镜像端口">
          <label>{{image.port}}</label>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleImageOk">确定</el-button>
          <el-button size="small" @click="handleImageCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div v-show="isNetwork">
      <el-form ref="networkForm" :model="network" label-width="80px">
        <el-form-item label="网卡名称">
          <el-autocomplete v-model="searchNetworkName" size="small" placeholder="网卡名称"
                           :fetch-suggestions="querySearchNetworkAsync" @select="handleNetworkSelect"></el-autocomplete>
        </el-form-item>
        <el-form-item label="子网">
          <el-input size="small" v-model="network.subnet" disabled></el-input>
        </el-form-item>
        <el-form-item label="网关">
          <el-input size="small" v-model="network.gateway" disabled></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" @click="handleNetworkOk">确定</el-button>
          <el-button size="small" @click="handleNetworkCancel">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
    <i  class="topoAttrArrow"
        :class="{'pushIcon':!isTopoAttrShow,'pullIcon':isTopoAttrShow}"
        @click="isTopoAttrShow =!isTopoAttrShow">
      <img :src="pushSvg" v-if="!isTopoAttrShow">
      <img :src="pullSvg" v-else>
    </i>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ImgList } from '@/api/docker'
import { NetWorkList } from '@/api/network'
import pushSvg from '@/assets/topo/push.svg'
import pullSvg from '@/assets/topo/pull.svg'

const props = defineProps({
  vSelectNodeData: {
    type: Object,
    default: () => ({})
  }
})

const isTopoAttrShow = ref(false)
const isContainer = ref(false)
const isNetwork = ref(false)
const imageList = ref([])
const networkList = ref([])
const searchImageName = ref("")
const searchNetworkName = ref("")
const image = reactive({
  id: '',
  vul_name: '',
  name: '',
  desc: '',
  port: '',
  open: false,
  raw: {}
})
const network = reactive({
  id: '',
  name: '',
  subnet: '',
  gateway: '',
  raw: {}
})

const nodeData = computed(() => {
  return JSON.parse(JSON.stringify(props.vSelectNodeData))
})

watch(() => props.vSelectNodeData, (val) => {
  isTopoAttrShow.value = false
  imageList.value = []
  isContainer.value = false
  isNetwork.value = false
  let nodeDataVal = JSON.parse(JSON.stringify(val))
  let nodeType = nodeDataVal["type"]
  if ('Container' === nodeType) {
    isContainer.value = true
    searchImageName.value = ""
    Object.assign(image, {
      id: '',
      vul_name: '',
      name: '',
      desc: '',
      port: '',
      open: false,
      raw: {}
    })
    if (JSON.stringify(nodeDataVal.attrs) !== '{}') {
      searchImageName.value = nodeDataVal.attrs.name
      Object.assign(image, nodeDataVal.attrs)
    }
  } else if ('Network' === nodeType) {
    isNetwork.value = true
    searchNetworkName.value = ""
    Object.assign(network, {
      id: '',
      name: '',
      subnet: '',
      gateway: '',
      raw: {}
    })
    if (JSON.stringify(nodeDataVal.attrs) !== '{}') {
      searchNetworkName.value = nodeDataVal.attrs.name
      Object.assign(network, nodeDataVal.attrs)
    }
  }
}, { immediate: true, deep: true })

function querySearchImageAsync(queryString, cb) {
  imageList.value = []
  if (queryString == null) {
    queryString = ""
  }
  ImgList(queryString, false, 1).then(response => {
    let results = response.data.results
    if (results !== null) {
      results.forEach((item) => {
        if (item.is_docker_compose === false) {
          imageList.value.push({"value": item["image_name"], "data": item})
        }
      });
    }
    if (imageList.value.length > 0) {
      cb(imageList.value);
    }
  })
}

function handleImageSelect(item) {
  let imageData = item.data
  searchImageName.value = item.value
  image.id = imageData.image_id
  image.vul_name = imageData.image_vul_name
  image.name = imageData.image_name
  image.desc = imageData.image_desc
  image.port = imageData.image_port
  image.raw = imageData
}

function querySearchNetworkAsync(queryString, cb) {
  networkList.value = []
  if (queryString == null) {
    queryString = ""
  }
  NetWorkList(queryString, 1).then(response => {
    let results = response.data.results
    if (results !== null) {
      results.forEach((item) => {
        networkList.value.push({"value": item["net_work_name"], "data": item})
      });
    }
    if (networkList.value.length > 0) {
      cb(networkList.value);
    }
  })
}

function handleNetworkSelect(item) {
  let networkData = item.data
  searchNetworkName.value = item.value
  network.id = networkData.net_work_id
  network.name = networkData.net_work_name
  network.gateway = networkData.net_work_gateway
  network.subnet = networkData.net_work_subnet
  network.raw = networkData
}

function handleImageOk() {
  if (image.id === '') {
    ElMessage({
      type: "error",
      message: "请选择镜像"
    });
  } else {
    props.vSelectNodeData.attrs = {...image}
    ElMessage({
      type: "success",
      message: "设置成功"
    });
    isTopoAttrShow.value = false
    imageList.value = []
    isContainer.value = false
    isNetwork.value = false
    searchImageName.value = ""
    Object.assign(image, {
      id: '',
      vul_name: '',
      name: '',
      desc: '',
      port: '',
      open: false
    })
  }
}

function handleImageCancel() {
  isTopoAttrShow.value = false
}

function handleNetworkOk() {
  if (network.id === '') {
    ElMessage({
      type: "error",
      message: "请选择网卡"
    });
  } else {
    props.vSelectNodeData.attrs = {...network}
    ElMessage({
      type: "success",
      message: "设置成功"
    });
    isTopoAttrShow.value = false
    isContainer.value = false
    isNetwork.value = false
    networkList.value = []
    searchImageName.value = ""
    Object.assign(network, {
      id: '',
      name: '',
      subnet: '',
      gateway: '',
      raw: {}
    })
  }
}

function handleNetworkCancel() {
  isTopoAttrShow.value = false
}
</script>

<style lang="less">

</style>
<style lang="less" scoped>
#topoAttrWrap{display:flex;flex-direction:column;height:100%;width:400px;position:absolute;top:0;right:-400px;background:#fff;border-left:1px solid darken(#f3f3f3,10%);transition:all 1s;box-sizing:border-box;
    &.active{right:0;box-shadow:-1px 0px 15px  #f3f3f3}
    .topoAttrArrow{color:#f3f3f3;font-size:20px;position:absolute;top:50%;translate:transform(0 -50%);z-index:200;cursor:pointer;
        &.pushIcon{left:-17px;}
        &.pullIcon{left:-2px;}
    }
    #topoAttrHeader{padding:10px 0;background-color:darken(#f3f3f3,5%);color:#525252;text-align:center;font-weight:400;font-size:14px;}
    .noAttrTip{padding:50px;text-align:center;flex:1;}
    .topoAttrBody{flex:1;display:flex;flex-direction:column;
        .topoAttrMain{overflow-y: scroll;flex:1;padding:20px 15px;box-sizing:border-box;}
        .topoAttrFooter{padding:30px 0;display:flex;justify-content: center;align-items:center;}
    }
}
</style>
