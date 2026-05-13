module BuildTasks
  extend Rake::DSL

  task :build do
    require "erb"
    require "fileutils"

    Dir.glob("source/**/*").each do |source|
      dest = source.sub(%r{\Asource/}, "skills/")
      destdir = File.dirname(dest)
      next if dest == source
      next if File.directory?(source)

      puts "== #{source}"

      original = File.read(source)
      erb = ERB.new(original)
      built = erb.result(binding)

      FileUtils.mkdir_p(destdir)
      File.write(dest, built)
    rescue => e
      puts "ERROR: #{source}"
      puts e
      next
    end
  end
end
