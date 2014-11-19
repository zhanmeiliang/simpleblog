from django.shortcuts import render
from .models import Post, Comment, Tag, Category
from django.shortcuts import render, get_object_or_404
from .forms import PostForm
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Count


def post_list(request):
    """所有已发布文章"""
    posts = Post.objects.filter(published_date__isnull=False).prefetch_related(
        'category').prefetch_related('tags').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_list_by_tag(request, tag):
    """根据标签列出已发布文章"""
    posts = Post.objects.filter(published_date__isnull=False, tags__name=tag).prefetch_related(
        'category').prefetch_related('tags').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_list_by_category(request, cg):
    """根据目录列表已发布文章"""
    posts = Post.objects.filter(published_date__isnull=False, category__name=cg).prefetch_related(
        'category').prefetch_related('tags').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_list_by_ym(request, y, m):
    """根据年月份列出已发布文章"""
    posts = Post.objects.filter(published_date__isnull=False, published_date__year=y,
                                published_date__month=m).prefetch_related(
        'category').prefetch_related('tags').order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.published_date:
        post.click += 1
        post.save()
    return render(request, 'blog/post_detail.html', {'post': post})


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # 开始处理标签
            tags = request.POST['tags'].split(',')
            all_tags = []
            if tags and len(tags) > 0:
                for tag in tags:
                    try:
                        t = Tag.objects.get(name=tag)
                    except Tag.DoesNotExist:
                        t = Tag(name=tag)
                        t.save()
                    all_tags.append(t)
            post.save()
            for tg in all_tags:
                post.tags.add(tg)
            return redirect('blog.views.post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form, 'is_new': True})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # 开始处理标签
            tags = request.POST['tags'].split(',')
            all_tags = []
            if tags and len(tags) > 0:
                for tag in tags:
                    try:
                        t = Tag.objects.get(name=tag)
                    except Tag.DoesNotExist:
                        t = Tag(name=tag)
                        t.save()
                    all_tags.append(t)
            post.save()
            post.tags.clear()
            # 文章的新标签更新
            for tg in all_tags:
                post.tags.add(tg)
            # 移除随风漂流的标签
            Tag.objects.annotate(num_post=Count('post')).filter(num_post=0).delete()
            return redirect('blog.views.post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    tags = ','.join([t.name for t in post.tags.all()])
    return render(request, 'blog/post_edit.html', {'form': form, 'tags': tags})


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('-created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('blog.views.post_detail', pk=pk)


@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('blog.views.post_list')

