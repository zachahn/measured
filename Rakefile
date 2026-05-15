class RakeTaskFailure
  attr_accessor :task_name
  attr_accessor :path
  attr_accessor :message

  def self.all
    @failures ||= []
  end

  def self.create(...)
    all.push(new(...))
  end

  def initialize(task_name, path, message)
    self.task_name = task_name
    self.path = path
    self.message = message
  end
end

at_exit do
  RakeTaskFailure.all.each do |f|
    puts "==> #{f.path}"
    puts "--> #{f.message}"
  end
end

module TestTasks
  extend Rake::DSL

  task :test do
    require "yaml"

    failures = []

    Dir.glob("source/skills/**/SKILL.md").each do |path|
      failures += check_name(path, File.basename(File.dirname(path)))
    rescue => e
      failures.push("ERROR: #{path} -- #{e.message}")
      next
    end

    Dir.glob("source/agents/*.md").each do |path|
      failures += check_name(path, File.basename(path, ".md"))
    rescue => e
      failures.push("ERROR: #{path} -- #{e.message}")
      next
    end

    if failures.empty?
      puts "All skill and agent names match."
    else
      failures.each { |f| puts "FAIL: #{f}" }
      abort "#{failures.size} file(s) failed validation"
    end

    sh "python3 test/test_ticket_lib.py"

    puts "[test] done"
  end

  def self.check_name(path, expected_name)
    content = File.read(path)
    unless content.start_with?("---\n")
      return ["#{path}: missing YAML frontmatter"]
    end

    _, frontmatter, _ = content.split(/^---\s*$/, 3)
    frontmatter = YAML.load(frontmatter)

    actual_name = frontmatter["name"]

    if actual_name.nil?
      ["#{path}: missing `name` in frontmatter"]
    elsif actual_name != expected_name
      ["#{path}: name `#{actual_name}` does not match expected `#{expected_name}`"]
    else
      []
    end
  end
end

module BuildTasks
  extend Rake::DSL

  def self.partials(path)
    @partials ||= {}
    @partials[path] ||= File.read(File.join("source/_partials", path))
  end

  def self.root
    Pathname.new(__dir__)
  end

  task :build do
    require "erb"
    require "fileutils"
    require "pathname"

    Dir.glob("source/**/*").each do |source|
      dest = source.sub(%r{\Asource/}, "")
      destdir = File.dirname(dest)
      next if dest == source
      next if File.directory?(source)
      next if source.start_with?("source/_")

      original = File.read(source)
      erb = ERB.new(original)
      built = erb.result(binding)

      FileUtils.mkdir_p(destdir)
      File.write(dest, built)
    rescue => e
      RakeTaskFailure.create(:build, source, e.message)
      next
    end

    puts "[build] done"
  end
end

task default: [:test, :build]
