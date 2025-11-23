i<script setup lang="ts">
import { ref } from 'vue'

import TextEditor from '../components/TextEditor.vue';

// technically this is not necessary, because the editor just initialises itself with this
// string, but apparently we  can end up  with desynchronised variables if we don't override the value
// of a property with a default value in the child
// see the warning here
// https://vuejs.org/guide/components/v-model.html#under-the-hood
// besides, we will probably want to pass some string into an editor, e.g.  when editing an existing note
// so that is probably how we would do that
const editorDefaultContent = ref('<p>ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ<p>')

    

</script>

<template>
  <div class="max-w-max mx-auto">
    <!-- mb for spacing underneath heading-->
    <h1 class="text-4xl font-bold mb-8">Journal</h1>
    <!-- v-model basically means -->
    <!--"The child component gets passed this variable-->
    <!-- and when it modified its copy, the parent copy is also modified" -->
    <!-- https://vuejs.org/guide/components/v-model -->
    <!-- for this to work, the child has to do some stuff as well, see-->
    <!-- https://vuejs.org/api/sfc-script-setup.html#definemodel-->
    <!-- directly putting an HTML string in here was annoying, hence variable -->
    <!-- multiple v-model:variable pairs can be passed-->
    <text-editor v-model:defaultContent="editorDefaultContent"/>
  </div>
</template>