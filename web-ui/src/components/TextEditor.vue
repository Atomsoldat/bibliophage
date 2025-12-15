<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Icon } from '@iconify/vue'
import { Editor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import Image from '@tiptap/extension-image'
// we only import this for type checking
// will not be bundled in final JS
import type { Level } from '@tiptap/extension-heading'

// in earlier versions of vue, you had to use defineProps()
// https://vuejs.org/api/sfc-script-setup.html#defineprops-defineemits
// and define emits and invoke onUpdate functions to pass values
// between parent and child; but thats not needed anymore
// see stuff below

// we can set up multiple variables by invoking defineModel() multiple times
// https://vuejs.org/api/sfc-script-setup.html#definemodel
// walliþ nu, gaþankōz"
// double consontant represented by single laguz
// Runic inscription moved to background watermark (see CSS below)
const defaultContent = defineModel('defaultContent', { type: String, default: ""})
  
  
// until we have instantiated the editor, it might be null
const editor = ref<Editor | null>(null)

// Track whether we're in WYSIWYG mode or raw markdown mode
type ViewMode = 'wysiwyg' | 'markdown'
const viewMode = ref<ViewMode>('markdown')

// when this component is mounted (basically when someone wants to see it)
// we instantiate the editor
// this is how the Tiptap people do it in their examples and source code
// https://github.com/ueberdosis/tiptap
onMounted(() => {
  editor.value = new Editor({
    extensions: [
      StarterKit,
      Markdown.configure({
        // Enable markdown serialization
        html: false,
        transformPastedText: true,
      }),
      Image,
    ],
    content: defaultContent.value,
    // Parse initial content as markdown
    contentType: 'markdown',
    onUpdate: ({ editor }) => {
      // Extract markdown from editor and sync back to the model
      // This enables parent components to receive markdown via v-model
      // In Tiptap v3, use editor.getMarkdown() directly
      const markdown = editor.getMarkdown()
      defaultContent.value = markdown
    },
  })
})


const linkUrl = ref('')
const showLinkInput = ref(false)

// Track active states for buttons
// computed() means, that the value of these variables is computed
// based on the function body provided whenever any of the dependencies
// in the body change
// https://vuejs.org/guide/essentials/computed.html#computed-properties
const activeMarks = computed(() => {
  if (!editor) return {}
  return {
    bold: editor.value?.isActive('bold'),
    italic: editor.value?.isActive('italic'),
    underline: editor.value?.isActive('underline'),
    code: editor.value?.isActive('code'),
    strike: editor.value?.isActive('strike'),
  }
})

const activeBlocks = computed(() => {
  if (!editor) return {}
  return {
    bulletList: editor.value?.isActive('bulletList'),
    orderedList: editor.value?.isActive('orderedList'),
    blockquote: editor.value?.isActive('blockquote'),
    codeBlock: editor.value?.isActive('codeBlock'),
  }
})

// Heading levels
const currentHeading = computed(() => {
  if (!editor) return null
  for (let level = 1; level <= 6; level++) {
    if (editor.value?.isActive('heading', { level })) return level
  }
  return null
})

// we use chain() to call multiple commands with one invocation
// https://tiptap.dev/docs/editor/api/editor#chain
const setHeading = (level: Level) => {
  editor.value?.chain().focus().toggleHeading({ level }).run()
}

// Link handling
const openLinkDialog = () => {
  const previousUrl = editor.value?.getAttributes('link').href
  linkUrl.value = previousUrl || ''
  showLinkInput.value = true
}

const setLink = () => {
  if (linkUrl.value === '') {
    editor.value?.chain().focus().extendMarkRange('link').unsetLink().run()
  } else {
    editor.value?.chain().focus().extendMarkRange('link').setLink({ href: linkUrl.value }).run()
  }
  showLinkInput.value = false
}

const removeLink = () => {
  editor.value?.chain().focus().unsetLink().run()
  showLinkInput.value = false
}

// Image handling
// TODO: we want to have proper image upload in the future
const addImage = () => {
  const url = prompt('Enter image URL:')
  if (url) {
    editor.value?.chain().focus().setImage({ src: url }).run()
  }
}

// Mode toggling between WYSIWYG and raw markdown
const toggleViewMode = () => {
  if (viewMode.value === 'markdown') {
    // Switching to WYSIWYG: recreate the editor to properly parse markdown
    // Store the markdown content before recreating
    const markdownContent = defaultContent.value

    // Destroy existing editor and recreate with markdown content
    // This ensures the Markdown extension properly parses the markdown syntax
    editor.value?.destroy()
    editor.value = new Editor({
      extensions: [
        StarterKit,
        Markdown.configure({
          html: false,
          transformPastedText: true,
        }),
        Image,
      ],
      content: markdownContent,
      // Tell Tiptap to parse content as markdown, not HTML
      contentType: 'markdown',
      onUpdate: ({ editor }) => {
        const markdown = editor.getMarkdown()
        defaultContent.value = markdown
      },
    })

    viewMode.value = 'wysiwyg'
  } else {
    // Switching to markdown: first extract current markdown from editor
    if (editor.value) {
      const currentMarkdown = editor.value.getMarkdown()
      defaultContent.value = currentMarkdown
    }
    viewMode.value = 'markdown'
  }
}

// Handle textarea changes in markdown mode
const handleMarkdownInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  defaultContent.value = target.value
}

// Expose methods that parent components can call
defineExpose({
  // Reset editor content to a specific value (or back to default)
  resetContent(passedContent?: string) {
    const newContent = passedContent ?? defaultContent.value
    editor.value?.commands.setContent(newContent)
  }
})

// Cleanup
onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="rich-text-editor w-full">
    <!-- Menubar -->
    <div class="mb-4 p-3 bg-base-200 rounded-t-lg flex flex-wrap gap-1">

      <!-- View Mode Toggle -->
      <button
        @click="toggleViewMode"
        class="btn btn-sm btn-primary"
        :title="viewMode === 'markdown' ? 'Switch to WYSIWYG mode' : 'Switch to markdown mode'"
      >
        <Icon v-if="viewMode === 'markdown'" icon="mdi:eye" />
        <Icon v-else icon="mdi:code-tags" />
        <span v-if="viewMode === 'markdown'">Preview</span>
        <span v-else>Source</span>
      </button>

      <!-- Formatting buttons only visible in WYSIWYG mode -->
      <template v-if="viewMode === 'wysiwyg'">
        <div class="divider divider-horizontal mx-0"></div>

        <!-- Text Formatting -->
        <button
        @click="editor?.chain().focus().toggleBold().run()"
        :class="{ 'btn-active': activeMarks.bold }"
        class="btn btn-sm btn-ghost"
        title="Bold"
      >
        <Icon icon="mdi:format-bold" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleItalic().run()"
        :class="{ 'btn-active': activeMarks.italic }"
        class="btn btn-sm btn-ghost"
        title="Italic"
      >
        <Icon icon="mdi:format-italic" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleUnderline().run()"
        :class="{ 'btn-active': activeMarks.underline }"
        class="btn btn-sm btn-ghost"
        title="Underline"
      >
        <Icon icon="mdi:format-underline" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleStrike().run()"
        :class="{ 'btn-active': activeMarks.strike }"
        class="btn btn-sm btn-ghost"
        title="Strikethrough"
      >
        <Icon icon="mdi:format-strikethrough" />
      </button>
      
      <div class="divider divider-horizontal mx-0"></div>
      
      <!-- Headings -->
      <div class="dropdown">
        <button
          tabindex="0"
          class="btn btn-sm btn-ghost"
          title="Heading level"
        >
          H <Icon icon="mdi:chevron-down" class="w-4 h-4" />
        </button>
        <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow border border-base-300">
          <li v-for="level in 6" :key="level">
            <a
              @click="setHeading(level as Level)"
              :class="{ 'active': currentHeading === level }"
            >
              Heading {{ level }}
            </a>
          </li>
        </ul>
      </div>
      
      <div class="divider divider-horizontal mx-0"></div>
      
      <!-- Lists & Blocks -->
      <button
        @click="editor?.chain().focus().toggleBulletList().run()"
        :class="{ 'btn-active': activeBlocks.bulletList }"
        class="btn btn-sm btn-ghost"
        title="Bullet List"
      >
        <Icon icon="mdi:format-list-bulleted" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleOrderedList().run()"
        :class="{ 'btn-active': activeBlocks.orderedList }"
        class="btn btn-sm btn-ghost"
        title="Ordered List"
      >
        <Icon icon="mdi:format-list-numbered" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleBlockquote().run()"
        :class="{ 'btn-active': activeBlocks.blockquote }"
        class="btn btn-sm btn-ghost"
        title="Blockquote"
      >
        <Icon icon="mdi:format-quote-close" />
      </button>
      
      <button
        @click="editor?.chain().focus().toggleCodeBlock().run()"
        :class="{ 'btn-active': activeBlocks.codeBlock }"
        class="btn btn-sm btn-ghost"
        title="Code Block"
      >
        <Icon icon="mdi:code-braces" />
      </button>
      
      <div class="divider divider-horizontal mx-0"></div>
      
      <!-- Link & Image -->
      <button
        @click="openLinkDialog"
        class="btn btn-sm btn-ghost"
        title="Add Link"
      >
        <Icon icon="mdi:link" />
      </button>
      
      <button
        @click="addImage"
        class="btn btn-sm btn-ghost"
        title="Add Image"
      >
        <Icon icon="mdi:image" />
      </button>
      
      <div class="divider divider-horizontal mx-0"></div>
      
      <!-- Undo/Redo -->
      <button
        @click="editor?.chain().focus().undo().run()"
        :disabled="!editor?.can().undo()"
        class="btn btn-sm btn-ghost"
        title="Undo"
      >
        <Icon icon="mdi:undo" />
      </button>
      
      <button
        @click="editor?.chain().focus().redo().run()"
        :disabled="!editor?.can().redo()"
        class="btn btn-sm btn-ghost"
        title="Redo"
      >
        <Icon icon="mdi:redo" />
      </button>
      </template>
    </div>
    
    <!-- Link Input Modal -->
    <div v-if="showLinkInput" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg">Edit Link</h3>
        <input
          v-model="linkUrl"
          type="text"
          placeholder="https://example.com"
          class="input input-bordered w-full mt-4"
        />
        <div class="modal-action">
          <button
            @click="setLink"
            class="btn btn-primary"
          >
            Save
          </button>
          <button
            @click="removeLink"
            class="btn btn-error"
          >
            Remove
          </button>
          <button
            @click="showLinkInput = false"
            class="btn"
          >
            Cancel
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="showLinkInput = false">close</button>
      </form>
    </div>
    
    <!-- Editor -->
    <div class="border border-t-0 border-base-300 rounded-b-lg overflow-hidden">
      <!-- Editor wrapper with runic watermark background -->
      <div class="relative bg-base-100">
        <!-- Runic watermark as actual element -->
        <!-- walliþ nu, gaþankōz" -->
        <!-- double consontant represented by single laguz -->
        <!-- ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ -->
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <div class="text-base-200 font-serif text-3xl font-light tracking-[0.3em]">
            ᚹᚨᛚᛁᚦᚾᚢᚷᚨᚦᚨᚾᚲᛟᛉ
          </div>
        </div>

        <!-- WYSIWYG Mode: Rich text editor -->
        <EditorContent
          v-if="viewMode === 'wysiwyg' && editor"
          v-bind:editor="(editor as Editor)"
          class="ProseMirror prose max-w-none focus:outline-none p-4 min-h-96 bg-transparent relative z-10"
        />

        <!-- Markdown Mode: Plain textarea -->
        <textarea
          v-else
          :value="defaultContent"
          @input="handleMarkdownInput"
          class="textarea textarea-bordered w-full min-h-96 font-mono text-sm p-4 bg-transparent rounded-none border-0 focus:outline-none resize-none relative z-10"
          spellcheck="false"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.ProseMirror) {
  outline: none;

  /* Heading styles */
  h1, h2 {
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
  }

  h1 {
    font-size: 1.4rem;
    font-weight: bold;
  }

  h2 {
    font-size: 1.2rem;
    font-weight: bold;
  }

  h3, h4, h5, h6 {
    font-weight: bold;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
  }

  /* List styles */
  ul, ol {
    padding: 0 1rem;
    margin: 1.25rem 1rem 1.25rem 0.4rem;
  }

  li {
    margin: 0.25rem 0;
  }

  /* Blockquote */
  blockquote {
    border-left: 3px solid #999;
    margin: 1.5rem 0;
    padding-left: 1rem;
  }

  /* Code */
  code {
    background-color: #f1f1f1;
    border-radius: 0.25rem;
    padding: 0.25em 0.3em;
    font-size: 0.85rem;
  }

  pre {
    background: #222;
    color: #fff;
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin: 1rem 0;
  }

  pre code {
    background: none;
    color: inherit;
    padding: 0;
  }
}

:deep(.ProseMirror:focus) {
  outline: none;
}

:deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}
</style>